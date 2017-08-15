import logging

import django.db.models.lookups
import re
from django.core.exceptions import FieldError
from django.core.files import File
from django.db.models import AutoField
from django.db.models.fields.files import FieldFile
from django.db.models.sql.where import WhereNode
from rdflib import URIRef, RDF, Literal

from fedoralink.db.binary import FedoraBinaryStream
from fedoralink.db.lookups import FedoraIdColumn, FedoraMetadataAnnotation
from fedoralink.db.queries import SearchQuery, InsertQuery, InsertScanner, FedoraQueryByPk, FedoraUpdateQuery
from fedoralink.db.utils import rdf2search
from fedoralink.idmapping import url2id, id2url
from fedoralink.manager import FEDORA_REPOSITORY
from fedoralink.models import FedoraOptions, FedoraObject
from .elasticsearch_connection import ElasticsearchConnection
from .fedora_connection import FedoraConnection

log = logging.getLogger(__file__)


class FedoraWithElasticConnection:
    def __init__(self, *args, **kwargs):
        self.fedora_connection = FedoraConnection(*args, **kwargs)
        self.elasticsearch_connection = ElasticsearchConnection(*args, **kwargs)
        self.options = {}

    def set_option(self, option_name, option_value):
        self.options[option_name] = option_value

    def disconnect(self):
        pass



    def execute_insert(self, query):
        ids = self.fedora_connection.create_resources(query)
        self.elasticsearch_connection.index_resources(query, ids)
        return InsertScanner([[url2id(object_id) for object_id in ids]])

    def execute_update(self, query):
        self.fedora_connection.update(query)
        self.elasticsearch_connection.update(query)
        return 1        # 1 row modified

    # noinspection PyUnusedLocal
    def execute(self, query, params=None):
        if isinstance(query, FedoraQueryByPk):
            return self.fedora_connection.execute_search_by_pk(query)
        elif isinstance(query, SearchQuery):
            return self.elasticsearch_connection.execute_search(query)
        elif isinstance(query, InsertQuery):
            return self.execute_insert(query)
        elif isinstance(query, FedoraUpdateQuery):
            return self.execute_update(query)
        elif isinstance(query, str) and re.search(u'ALTER TABLE .* ADD CONSTRAINT.* UNIQUE', query):
            log.warning('Adding unique constraints is not supported on Fedora, ignoring')
        else:
            raise NotImplementedError('Query of type %s is not yet implemented: %s' % (type(query), query))

    def create_model(self, django_model):
        fedora_options = FedoraWithElasticConnection.prepare_fedora_options(django_model._meta)
        if not FedoraObject.objects.filter(fedora_id=django_model._meta.db_table).exists():
            self.fedora_connection.create_resources(InsertQuery(
                [
                    {
                        'parent': None,
                        'bitstream': None,
                        'fields': {
                        },
                        'slug': django_model._meta.db_table,
                        'doc_type': None,
                        'options': None,
                    }
                ]
            ))

        self.elasticsearch_connection.update_elasticsearch_index(django_model)

    def delete_all_data(self):
        self.fedora_connection.delete_all_data()
        self.elasticsearch_connection.delete_all_data()

    def get_query_representation(self, query, compiler, connection):
        opts = query.get_meta()
        FedoraWithElasticConnection.prepare_fedora_options(opts)

        extra_select, order_by, group_by = compiler.pre_sql_setup()
        distinct_fields = compiler.get_distinct()

        pk = self.is_fedora_query_by_pk(query, compiler, connection)
        fedora_via = getattr(query, 'fedora_via', None)
        if pk and (fedora_via is None or fedora_via == FEDORA_REPOSITORY) :
            return FedoraQueryByPk(query, pk, compiler), []
        return self.elasticsearch_connection.get_query_representation(query, compiler, extra_select,
                                                                      order_by, group_by, distinct_fields)

    def get_update_representation(self, query, compiler, connection):
        opts = query.get_meta()
        FedoraWithElasticConnection.prepare_fedora_options(opts)

        compiler.pre_sql_setup()

        pk = self.is_fedora_query_by_pk(query, compiler, connection)
        if not pk:
            raise NotImplementedError('Update defined by custom search is not supported yet. '
                                      'The only supported update is for objects defined by pk')

        update_data, prev_data = self._object_to_update_data(pk, compiler)

        return FedoraUpdateQuery(pk, update_data, prev_data, compiler.query.patched_instance), []

    def commit(self):
        log.warning('commit and rollback are not supported yet on fedora connection ...')
        pass

    def rollback(self):
        log.warning('commit and rollback are not supported yet on fedora connection ...')
        pass

    @staticmethod
    def get_insert_representation(query, compiler):
        opts = query.get_meta()

        FedoraWithElasticConnection.prepare_fedora_options(opts)

        has_fields = bool(query.fields)
        fields = query.fields if has_fields else [opts.pk]

        # TODO: rdf_type
        if has_fields:
            value_rows = [
                FedoraWithElasticConnection._object_to_insert_data(opts, obj, fields, compiler)
                for obj in query.objs
            ]
        else:
            value_rows = [{} for _ in query.objs]

        yield InsertQuery(value_rows), {}

    @staticmethod
    def _object_to_insert_data(opts, obj, fields, compiler):
        ret = {
            'parent': getattr(obj, '_fedora_parent', None),
            'bitstream': getattr(obj, 'fedora_binary_stream', None),
            'doc_type': rdf2search(opts.fedora_options.primary_rdf_type),
            'fields': {
                (field.fedora_options.rdf_name, field.fedora_options.search_name):
                    compiler.prepare_value(field, compiler.pre_save_val(field, obj))
                for field in fields if hasattr(field, 'fedora_options')
            },
            'options': opts.fedora_options
        }
        ret['fields'][(RDF.type, rdf2search('rdf_type'))] = [URIRef(x) for x in opts.fedora_options.rdf_types]
        return ret

    def _object_to_update_data(self, pk, compiler):
        ret = {}
        prev = {}
        previous_update_values = compiler.query.previous_update_values
        if previous_update_values is None:
            fetched_obj = FedoraObject.objects.get(pk=pk)
            previous_update_values = fetched_obj.fedora_meta
            compiler.query.previous_update_values = previous_update_values
            compiler.query.patched_instance = fetched_obj
        for field, model, val in compiler.query.values:
            if hasattr(val, 'resolve_expression'):
                val = val.resolve_expression(compiler.query, allow_joins=False, for_save=True)
                if val.contains_aggregate:
                    raise FieldError("Aggregate functions are not allowed in this query")
            elif hasattr(val, 'prepare_database_save'):
                if field.remote_field:
                    val = field.get_db_prep_save(
                        val.prepare_database_save(field),
                        connection=compiler.connection,
                    )
                else:
                    raise TypeError(
                        "Tried to update field %s with a model instance, %r. "
                        "Use a value compatible with %s."
                        % (field, val, field.__class__.__name__)
                    )
            else:
                val = field.get_db_prep_save(val, connection=compiler.connection)

            ret[(field.fedora_options.rdf_name, field.fedora_options.search_name)] = val
            prev_data = previous_update_values.get(field.name, None)
            if prev_data and isinstance(prev_data, File):
                prev_data = URIRef(prev_data.name)
            prev[(field.fedora_options.rdf_name, field.fedora_options.search_name)] = \
                prev_data

        return ret, prev

    @staticmethod
    def prepare_fedora_options(opts):
        if not hasattr(opts, 'fedora_options'):
            opts.fedora_options = FedoraOptions(opts.model)
        return opts.fedora_options

    def is_fedora_query_by_pk(self, query, compiler, connection):
        has_annotations = (
            query.annotations and
            (
                len(query.annotations) > 1 or
                not isinstance(list(query.annotations.values())[0], FedoraMetadataAnnotation)
            )
        )
        if has_annotations or query.extra or query.extra_order_by \
                or query.extra_select or query.extra_tables or query.select:
            return None
        if not isinstance(query.where, WhereNode):
            raise NotImplementedError("Expecting where to be instance of WhereNode")
        where = query.where
        if len(where.children) != 1:
            return None
        lookup = where.children[0]
        if not isinstance(lookup, django.db.models.lookups.Exact):
            return None
        lhs, lhs_params = lookup.process_lhs(compiler, connection)
        rhs, rhs_params = lookup.process_rhs(compiler, connection)

        if isinstance(lhs, FedoraIdColumn):
            if not isinstance(rhs, str) and not isinstance(rhs, URIRef):
                raise AttributeError('In fedora_id=... query, the right hand side '
                                     'must be an instance of string or URIRef')

            return str(rhs)
        # someone is searching via .get(pk=...) or .get(id=...)
        elif isinstance(lhs.django_field, AutoField) and lhs.django_field.model._meta.pk == lhs.django_field:
            return id2url(rhs)

        return None

    def fetch_bitstream(self, url):
        return self.fedora_connection.fetch_bitstream(url)