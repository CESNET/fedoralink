import logging

import django.db.models.lookups
from django.db.models.sql.where import WhereNode
from rdflib import URIRef

from fedoralink.db.lookups import FedoraIdColumn
from fedoralink.db.queries import SearchQuery, InsertQuery, InsertScanner, FedoraQueryByPk
from fedoralink.idmapping import url2id
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
        return InsertScanner([url2id(object_id) for object_id in ids])

    # noinspection PyUnusedLocal
    def execute(self, query, params=None):
        if isinstance(query, FedoraQueryByPk):
            return self.fedora_connection.execute_search_by_pk(query)
        elif isinstance(query, SearchQuery):
            return self.elasticsearch_connection.execute_search(query)
        elif isinstance(query, InsertQuery):
            return self.execute_insert(query)
        else:
            raise NotImplementedError('This type of query is not yet implemented')

    def create_model(self, django_model):
        FedoraWithElasticConnection.prepare_fedora_options(django_model._meta)
        # create the collection for the model in fedora TODO: try to get the resource if it exists
        if not FedoraObject.objects.filter(fedora_id=django_model._meta.db_table).exists():
            self.fedora_connection.create_resources(InsertQuery(
                    [
                        {
                            'parent': None,
                            'fields': {
                            },
                            'slug': django_model._meta.db_table,
                            'doc_type': None
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
        if pk:
            return FedoraQueryByPk(query, pk, compiler), []
        return self.elasticsearch_connection.get_query_representation(query, compiler, extra_select,
                                                                      order_by, group_by, distinct_fields)

    def commit(self):
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
                {
                    'parent': getattr(obj, '_fedora_parent', None),
                    'doc_type': opts.db_table,
                    'fields': {
                        (field.fedora_options.rdf_name, field.fedora_options.search_name):
                            compiler.prepare_value(field, compiler.pre_save_val(field, obj))
                        for field in fields if hasattr(field, 'fedora_options')
                    }
                }
                for obj in query.objs
            ]
        else:
            value_rows = [{} for _ in query.objs]

        yield InsertQuery(value_rows), {}

    @staticmethod
    def prepare_fedora_options(opts):
        if not hasattr(opts, 'fedora_options'):
            opts.fedora_options = FedoraOptions(opts.model)
        return opts.fedora_options

    def is_fedora_query_by_pk(self, query, compiler, connection):
        if query.annotation_select or query.annotations or query.extra or query.extra_order_by \
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

        return None

