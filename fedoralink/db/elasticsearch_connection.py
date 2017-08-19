import json
import logging
import urllib.parse
from random import random

import cachetools
import django.db.models as django_fields
import elasticsearch.helpers
from django.db.models import Count
from django.db.models.expressions import Col
from elasticsearch import Elasticsearch

from fedoralink.db.lookups import get_column_ids, Operation, Column, Node
from fedoralink.db.queries import SearchQuery, SelectScanner
from fedoralink.db.utils import rdf2search
from fedoralink.fields import FedoraField
from fedoralink.idmapping import id2url
from fedoralink.manager import ELASTICSEARCH
from fedoralink.models import FedoraResourceUrlField, FedoraObject
from . import FedoraError

log = logging.getLogger(__file__)


class IndexMappingError(FedoraError):
    pass


class InconsistentSearchError(FedoraError):
    pass


class FuzzyTTLCache(cachetools.TTLCache):
    """
    cachetools.TTLCache has a ttl as one of the parameters. However if we fetched objects
    of different types during a single FedoraObject.objects.filter(...) call, they would be removed from the cache
    at the same time. That would mean that after that time a similar request would need to update all the cached 
    mappings. To distribute mapping requests in time, FuzzyTTL does not give a single ttl value but a value 
    perturbed by a random delta.
    """

    def __init__(self, maxsize, ttl, delta):
        super().__init__(maxsize=maxsize, ttl=ttl)
        self.__base_ttl = ttl
        self.__ttl_delta = min(ttl - 1, delta)

    def __setitem__(self, key, value, cache_setitem=cachetools.Cache.__setitem__):
        self.__ttl = self.__base_ttl + (random() - 0.5) * 2 * self.__ttl_delta
        super().__setitem__(key, value, cache_setitem)


class ElasticsearchMappingCache:
    """
    When data are received from elasticsearch they are serialized as json that does not have any types
    apart from json default - number, string, bool, null. To be able to deserialize for example dates 
    or discriminate between floats and ints, we need to fetch the actual mapping which gives us the
    correct types.
    
    This class is a cache of fetched mappings indexed by doc_type
    """

    def __init__(self, connection):
        self.mapping_cache = FuzzyTTLCache(maxsize=512, ttl=5 * 60, delta=60)
        self.connection = connection

    def __delitem__(self, doc_type):
        try:
            del self.mapping_cache[doc_type]
        except KeyError:
            pass

    def __getitem__(self, doc_type):
        try:
            return self.mapping_cache[doc_type]
        except KeyError:
            pass

        mapping = self.connection.elasticsearch.indices.get_mapping(
            index=self.connection.elasticsearch_index_name,
            doc_type=doc_type)

        if self.connection.elasticsearch_index_name not in mapping:
            raise KeyError('Mapping not in the elasticsearch')
        mapping = mapping[self.connection.elasticsearch_index_name]
        mapping = mapping['mappings'][doc_type]['properties']
        self.mapping_cache[doc_type] = mapping
        return mapping


class ElasticsearchConnection(object):
    def __init__(self, *args, **kwargs):
        urls = kwargs['elasticsearch_url']
        self.namespace_config = kwargs['namespace_config']
        self.mapping_cache = ElasticsearchMappingCache(self)

        if isinstance(urls, str):
            urls = [urls]

        url = urllib.parse.urlsplit(urls[0])
        self.elasticsearch_index_name = url.path
        print(">>>", self.elasticsearch_index_name)
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
        print(">>> >>>", self.namespace_config.prefix)
        if self.namespace_config.prefix:
            self.elasticsearch_index_name += '_%s' % rdf2search(self.namespace_config.prefix)

        if not self.elasticsearch.indices.exists(self.elasticsearch_index_name):
            self.elasticsearch.indices.create(index=self.elasticsearch_index_name,
                                              body={
                                                  'settings': {
                                                      "index.mapper.dynamic": False
                                                  }
                                              })

        self.refresh()

    def refresh(self):
        self.elasticsearch.indices.refresh(index=self.elasticsearch_index_name)

    def update_elasticsearch_index(self, django_model):

        # doc_type is a primary rdf type
        doc_type = rdf2search(django_model._meta.fedora_options.primary_rdf_type)

        fields = django_model._meta.fields
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

        fields_names = set(mapping.keys())
        fields_names.update(new_mapping.keys())

        log.debug("%s : %s", mapping, new_mapping)
        changed = False

        for fld in fields_names:
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
            del self.mapping_cache[doc_type]
            self.refresh()

    @staticmethod
    def _fields_to_mapping(fields):
        mapping = {}
        for fld in fields:
            # do not index this field, as it is only a dummy ...
            if isinstance(fld, FedoraResourceUrlField) or isinstance(fld, django_fields.AutoField):
                continue

            name = fld.fedora_options.search_name
            if isinstance(fld, FedoraField):
                fld = fld.base_field
            if isinstance(fld, django_fields.AutoField):
                field_mapping = {
                    'type': 'keyword'
                }
            elif isinstance(fld, django_fields.DateTimeField):
                field_mapping = {
                    'type': 'date'
                }
            elif isinstance(fld, django_fields.DateField):
                field_mapping = {
                    'type': 'date'
                }
            elif isinstance(fld, django_fields.TimeField):
                # time gets translated to 00:00:00.00000000 and is compared as texts
                field_mapping = {
                    'type': 'keyword'
                }
            elif isinstance(fld, django_fields.DurationField):
                # duration gets translated to seconds and is indexed as double
                field_mapping = {
                    'type': 'double'
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
            elif isinstance(fld, django_fields.UUIDField):
                field_mapping = {
                    'type': 'keyword',
                }
            elif isinstance(fld, django_fields.GenericIPAddressField):
                field_mapping = {
                    'type': 'keyword',
                }
            elif isinstance(fld, django_fields.BooleanField):
                field_mapping = {
                    'type': 'boolean',
                }
            elif isinstance(fld, django_fields.NullBooleanField):
                field_mapping = {
                    'type': 'boolean',
                }
            elif isinstance(fld, django_fields.FloatField):
                field_mapping = {
                    'type': 'double',
                }
            elif isinstance(fld, django_fields.DecimalField):
                # TODO: there seems to be no support for decimals with arbitrary
                # TODO: precision in elasticsearch, consider scaled_float in some cases
                field_mapping = {
                    'type': 'double',
                }
            elif isinstance(fld, django_fields.BigIntegerField):
                # TODO: there is no support for biginteger in elasticsearch yet, so convert to string
                field_mapping = {
                    'type': 'keyword',
                }
            elif isinstance(fld, django_fields.IntegerField):
                field_mapping = {
                    'type': 'integer',
                }
            elif isinstance(fld, django_fields.BinaryField):
                continue
            elif isinstance(fld, django_fields.FileField):
                field_mapping = {
                    'type': 'keyword',
                }
            else:
                raise IndexMappingError('Field type %s (on field %s) is not supported' % (type(fld), name))

            mapping[name] = field_mapping

        mapping[rdf2search('rdf_type')] = {
            'type': 'keyword'
        }

        return mapping

    @staticmethod
    def get_query_representation(query, compiler, extra_select, order_by, group_by, distinct_fields):
        annotations = query.annotations.copy()
        annotations.pop('fedora_meta', None)
        add_count = None
        sort_by = [
            '_doc'
        ]
        if annotations:
            for annotation_key, annotation_value in annotations.items():
                if isinstance(annotation_value, Count):
                    add_count = annotation_key
                else:
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
            sort_by = []
            for order_el in order_by:
                order_el = order_el[0]
                if not isinstance(order_el.expression, Col):
                    raise NotImplementedError('Only columns are supported in ordering')
                order_field = order_el.expression.field
                if order_field.primary_key:
                    sort_by.append({
                        '_uid' : {
                            'order': 'desc' if order_el.descending else 'asc'
                        }
                    })
                else:
                    order_search_name = order_field.fedora_options.search_name
                    sort_by.append({
                        order_search_name : {
                            'order': 'desc' if order_el.descending else 'asc'
                        }
                    })
        if query.select_for_update:
            raise NotImplementedError("Select for update not yet implemented")
        if query.select_for_update_nowait:
            raise NotImplementedError("Select for update nowait not yet implemented")
        if query.select_related:
            raise NotImplementedError("Select related not yet implemented")
        if group_by:
            # just ignore primary keys ...
            for g in group_by:
                if isinstance(g[0], Column):
                    if g[0].django_field == g[0].django_field.model._meta.pk:
                        continue
                raise NotImplementedError("Group by not yet implemented")
        if distinct_fields:
            raise NotImplementedError("Distinct not yet implemented")

        model = query.model
        where = query.where

        query_parts = []

        rdf_types = model._meta.fedora_options.rdf_types

        if model != FedoraObject:
            for rdf_type in rdf_types:
                query_parts.append({
                    'term': {
                        rdf2search('rdf_type'): rdf_type
                    }
                })

        if where.children:
            tree, params = compiler.compile(where)
            query_parts.append(convert_tree_to_elastic(tree))

        elastic_query = {
            'query': {
                'bool': {
                    'must': query_parts
                },
            },
            'sort': sort_by
        }
        print(json.dumps(elastic_query, indent=4))

        return SearchQuery(elastic_query, get_column_ids(compiler.select, add_count),
                           compiler.query.low_mark, compiler.query.high_mark,
                           add_count), {}

    def execute_search(self, query):
        if not query.use_search_instead_of_scan and not query.start:
            return SelectScanner(
                elasticsearch.helpers.scan(
                    self.elasticsearch,
                    query=query.query,
                    scroll=u'1m',
                    preserve_order=True,
                    index=self.elasticsearch_index_name,
                    from_=query.start),
                query.columns, query.count,
                self.mapping_cache)
        else:
            result = self.elasticsearch.search(index=self.elasticsearch_index_name, body=query.query,
                                               from_=query.start, size=query.count if query.count else 1000)
            hits = result['hits']
            data = hits['hits']
            return SelectScanner(
                iter(data),
                query.columns, query.count,
                self.mapping_cache,
                result_metadata=hits
            )

    def index_resources(self, query, ids):
        from fedoralink.db.base import FedoraDatabase

        for obj, obj_id in zip(query.objects, ids):
            if not obj['doc_type']:
                continue
            serialized_object = {k[1]: v for k, v in obj['fields'].items()
                                            if k[1] is not None and not isinstance(v, FedoraDatabase.Binary)}
            self.elasticsearch.index(index=self.elasticsearch_index_name,
                                     doc_type=obj['doc_type'],
                                     id=obj_id, body=serialized_object)
        self.refresh()

    def delete_all_data(self):
        if self.elasticsearch.indices.exists(self.elasticsearch_index_name):
            self.elasticsearch.indices.delete(index=self.elasticsearch_index_name)

    def update(self, query):
        serialized_object = {k[1]: v for k, v in query.update_data.items()}
        try:
            mo = FedoraObject.objects.via(ELASTICSEARCH).get(fedora_id=query.pk)
        except:
            raise InconsistentSearchError('Could not find object instance in elasticsearch!')
        self.elasticsearch.update(index=self.elasticsearch_index_name,
                                  doc_type=mo.fedora_meta.doc_type,
                                  id=query.pk, body={'doc': serialized_object})
        self.refresh()


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
            lhs = tree.operands[0]
            rhs = tree.operands[1]
            if isinstance(rhs, Node):
                rhs = convert_tree_to_elastic(rhs)
            if isinstance(lhs, Column):
                if lhs.django_field.model._meta.pk == lhs.django_field:
                    if isinstance(rhs, int):
                        rhs = id2url(rhs)
                        return {
                            'term': {
                                '_id': rhs
                            }
                        }
            return {
                'term': {
                    convert_tree_to_elastic(tree.operands[0]): rhs
                }
            }

        if tree.type == 'in':
            lhs = tree.operands[0]
            rhs = tree.operands[1]
            if isinstance(rhs, Node):
                rhs = convert_tree_to_elastic(rhs)

            return {
                'bool': {
                    'minimum_should_match': 1,
                    'should': [
                        {
                            'term': {
                                convert_tree_to_elastic(lhs): r
                            }
                        } for r in rhs
                    ]
                }
            }

        raise NotImplementedError('Conversion of operation type %s to elasticsearch not yet implemented' % tree.type)
    elif isinstance(tree, Column):
        return tree.search_name
    else:
        raise NotImplementedError('Conversion of tree node %s to elasticsearch not yet implemented' % tree)
