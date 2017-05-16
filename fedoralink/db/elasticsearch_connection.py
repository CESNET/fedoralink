import json
import logging
import urllib.parse
from collections import OrderedDict

import django.db.models.fields as django_fields
import elasticsearch.helpers
from elasticsearch import Elasticsearch

from fedoralink.models import FedoraOptions
from . import FedoraError

log = logging.getLogger(__file__)


class IndexMappingError(FedoraError):
    pass


class ElasticQuery:
    def __init__(self, query):
        self.query = query


class FedoraInsert:
    def __init__(self, query):
        self.query = query


class ElasticsearchMixin(object):
    def __init__(self, *args, **kwargs):
        urls = kwargs['elasticsearch_url']

        if isinstance(urls, str):
            urls = [urls]

        url = urllib.parse.urlsplit(urls[0])
        self.elasticsearch_index_name = url.path

        while self.elasticsearch_index_name.startswith('/'):
            self.elasticsearch_index_name = self.elasticsearch_index_name[1:]

        while self.elasticsearch_index_name.endswith('/'):
            self.elasticsearch_index_name = self.elasticsearch_index_name[:-1]

        self.elasticsearch = Elasticsearch(hosts=[
            {
                "host": urllib.parse.urlsplit(x).hostname,
                "port": urllib.parse.urlsplit(x).port
            } for x in urls
        ])

        if not self.elasticsearch.indices.exists(self.elasticsearch_index_name):
            self.elasticsearch.indices.create(index=self.elasticsearch_index_name)

    def update_elasticsearch_index(self, django_model):

        ElasticsearchMixin._prepare_fedora_options(django_model._meta)

        fields = django_model._meta.fields
        doc_type = django_model._meta.label
        mapping = self.elasticsearch.indices.get_mapping(index=self.elasticsearch_index_name,
                                                         doc_type=doc_type)
        # default if the mapping does not exists yet
        mapping = mapping.get(
            self.elasticsearch_index_name,
            {
                'mappings': {
                    doc_type: {
                        'properties': {}
                    }
                }
            })
        mapping = mapping['mappings'][doc_type]['properties']

        new_mapping = self._fields_to_mapping(fields)

        fields = set(mapping.keys())
        fields.update(new_mapping.keys())

        log.debug("%s : %s", mapping, new_mapping)
        changed = False

        for fld in fields:
            if fld in mapping:
                if fld not in new_mapping:
                    raise IndexMappingError(
                        'Field removal not yet supported in elasticsearch - about to remove %s' % fld)
                else:
                    # compare and raise exception
                    if json.dumps(mapping[fld], sort_keys=True) != json.dumps(new_mapping[fld], sort_keys=True):
                        raise IndexMappingError(
                            'Field change not yet supported in elasticsearch - about to change %s from %s to %s' % (
                                fld, mapping[fld], new_mapping[fld]))
            else:
                changed = True

        if changed:
            log.warning("Updating index definition of %s in elasticsearch, do not forget to reindex afterwards",
                        doc_type)
            self.elasticsearch.indices.put_mapping(index=self.elasticsearch_index_name, doc_type=doc_type, body={
                'properties': new_mapping
            })

    @staticmethod
    def _fields_to_mapping(fields):
        mapping = {}
        for fld in fields:
            name = fld.fedora_options.search_name
            if isinstance(fld, django_fields.AutoField):
                field_mapping = {
                    'type': 'keyword'
                }
            elif isinstance(fld, django_fields.DateTimeField):
                field_mapping = {
                    'type': 'date'
                }
            elif isinstance(fld, django_fields.CharField):
                # TODO: check if there is a fulltext annotation there
                field_mapping = {
                    'type': 'keyword'
                }
            else:
                raise IndexMappingError('Field type %s (on field %s) is not supported' % (type(fld), name))

            mapping[name] = field_mapping

        return mapping

    @staticmethod
    def get_query_representation(query, compiler):
        opts = query.get_meta()
        ElasticsearchMixin._prepare_fedora_options(opts)

        extra_select, order_by, group_by = compiler.pre_sql_setup()
        distinct_fields = compiler.get_distinct()

        if query.annotations:
            raise NotImplementedError("Annotations not yet implemented")
        if query.extra:
            raise NotImplementedError("Extra not yet implemented")
        if query.extra_order_by:
            raise NotImplementedError("Extra Order By not yet implemented")
        if extra_select:
            raise NotImplementedError("Extra Select not yet implemented")
        if query.extra_select_mask:
            raise NotImplementedError("Extra Select Mask not yet implemented")
        if query.extra_tables:
            raise NotImplementedError("Extra Tables not yet implemented")
        if order_by:
            raise NotImplementedError("Order by not yet implemented")
        if query.select_for_update:
            raise NotImplementedError("Select for update not yet implemented")
        if query.select_for_update_nowait:
            raise NotImplementedError("Select for update nowait not yet implemented")
        if query.select_related:
            raise NotImplementedError("Select related not yet implemented")
        if group_by:
            raise NotImplementedError("Group by not yet implemented")
        if distinct_fields:
            raise NotImplementedError("Distinct not yet implemented")

        model = query.model
        where = query.where

        query = {
            'query': {
                'type': {
                    'value': model._meta.label
                }
            }
        }

        if where.children:
            raise NotImplementedError(".filter(), .exclude() not implemented")

        return ElasticQuery(query), {}

    def execute(self, query, params):
        if isinstance(query, ElasticQuery):
            return elasticsearch.helpers.scan(
                self.elasticsearch,
                query=query.query,
                scroll=u'1m',
                preserve_order=True,
                index=self.elasticsearch_index_name)
        elif isinstance(query, FedoraInsert):
            return self.execute_insert(query.query)
        else:
            raise NotImplementedError('This type of query is not yet implemented')

    def execute_insert(self, query):
        raise NotImplementedError('Insert not yet implemented')

    @staticmethod
    def get_insert_representation(query, compiler):
        opts = query.get_meta()

        ElasticsearchMixin._prepare_fedora_options(opts)

        has_fields = bool(query.fields)
        fields = query.fields if has_fields else [opts.pk]

        if has_fields:
            value_rows = [
                {
                    'doc_type': opts.label,
                    'fields': {
                        field.column: compiler.prepare_value(field, compiler.pre_save_val(field, obj))
                            for field in fields
                    }
                }
                for obj in query.objs
            ]
        else:
            value_rows = [{} for _ in query.objs]

        yield FedoraInsert(value_rows), {}

    @staticmethod
    def _prepare_fedora_options(opts):
        if not hasattr(opts, 'fedora_options'):
            opts.fedora_options = FedoraOptions(opts.model)
