import json
import logging
import urllib.parse

import django.db.models.fields as django_fields
import elasticsearch.helpers
from elasticsearch import Elasticsearch

from fedoralink.db.lookups import get_column_ids, Operation, Column, Node
from fedoralink.db.queries import SearchQuery, SelectScanner
from fedoralink.db.utils import rdf2search
from fedoralink.models import FedoraResourceUrlField, FedoraObject
from . import FedoraError

log = logging.getLogger(__file__)


class IndexMappingError(FedoraError):
    pass


class ElasticsearchConnection(object):
    def __init__(self, *args, **kwargs):
        urls = kwargs['elasticsearch_url']
        self.namespace_config = kwargs['namespace_config']

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

        if self.namespace_config.prefix:
            self.elasticsearch_index_name += '_%s' % rdf2search(self.namespace_config.prefix)

        if not self.elasticsearch.indices.exists(self.elasticsearch_index_name):
            self.elasticsearch.indices.create(index=self.elasticsearch_index_name)

    def update_elasticsearch_index(self, django_model):

        fields = django_model._meta.fields
        doc_type = django_model._meta.db_table
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
            # do not index this field, as it is only a dummy ...
            if isinstance(fld, FedoraResourceUrlField) or isinstance(fld, django_fields.AutoField):
                continue

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
            elif isinstance(fld, django_fields.TextField):
                # TODO: check if there is a fulltext annotation there
                # TODO: store=True?
                field_mapping = {
                    'type': 'keyword',
                }
            else:
                raise IndexMappingError('Field type %s (on field %s) is not supported' % (type(fld), name))

            mapping[name] = field_mapping

        mapping['rdf_type'] = {
            'type': 'keyword'
        }

        return mapping

    @staticmethod
    def get_query_representation(query, compiler, extra_select, order_by, group_by, distinct_fields):

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

        query_parts = []
        if type(model) != FedoraObject:
            query_parts.append({
                'type': {
                    'value': model._meta.db_table
                }
            })

        if where.children:
            tree, params = compiler.compile(where)
            query_parts.append(convert_tree_to_elastic(tree))

        query = {
            'query': {
                'bool': {
                    'must': query_parts
                }
            }
        }
        print(json.dumps(query, indent=4))

        return SearchQuery(query, get_column_ids(compiler.select),
                           compiler.query.low_mark, compiler.query.high_mark), {}

    def execute_search(self, query):
        return SelectScanner(
            elasticsearch.helpers.scan(
                self.elasticsearch,
                query=query.query,
                scroll=u'1m',
                preserve_order=True,
                index=self.elasticsearch_index_name,
                from_=query.start),
            query.columns, query.count)

    def index_resources(self, query, ids):
        for obj, obj_id in zip(query.objects, ids):
            if not obj['doc_type']:
                continue
            serialized_object = {k[1]: v for k, v in obj['fields'].items()}
            self.elasticsearch.index(index=self.elasticsearch_index_name,
                                     doc_type=obj['doc_type'],
                                     id=obj_id, body=serialized_object)  # wait_for_active_shards='all'

    def delete_all_data(self):
        if self.elasticsearch.indices.exists(self.elasticsearch_index_name):
            self.elasticsearch.indices.delete(index=self.elasticsearch_index_name)


def convert_tree_to_elastic(tree):
    if isinstance(tree, Operation):
        if tree.type == 'AND':
            return {
                'bool': {
                    'must': [
                        convert_tree_to_elastic(x) for x in tree.operands
                    ]
                }
            }
        if tree.type == 'OR':
            return {
                'bool': {
                    'should': [
                        convert_tree_to_elastic(x) for x in tree.operands
                    ],
                    'minimum_should_match': 1
                }
            }
        if tree.type == 'exact':
            rhs = tree.operands[1]
            if isinstance(rhs, Node):
                rhs = convert_tree_to_elastic(rhs)
            return {
                'term': {
                    convert_tree_to_elastic(tree.operands[0]): rhs
                }
            }

        raise NotImplementedError('Conversion of operation type %s to elasticsearch not yet implemented' % tree.type)
    elif isinstance(tree, Column):
        return tree.search_name
    else:
        raise NotImplementedError('Conversion of tree node %s to elasticsearch not yet implemented' % tree)
