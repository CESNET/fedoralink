import logging
import time
import unittest.util

import elasticsearch.helpers
from django.db import connections
from django.db.models import Q
from rdflib import URIRef

from fedoralink.fedorans import CESNET
from fedoralink.idmapping import url2id
from fedoralink.models import FedoraObject
from fedoralink.tests.testserver.testapp.models import Simple, Complex
from .utils import FedoraTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestSimpleStoreFetch(FedoraTestBase):

    def test_simple_store_fetch(self):
        o1 = Simple.objects.create(text='Hello world 1')
        self.assertIsNotNone(o1.id, 'Stored object must have an id')
        self.assertIsNotNone(o1.fedora_id, 'Stored object must have a fedora_id')
        self.assertEqual(o1.id, url2id(o1.fedora_id), 'The id of the stored and retrieved objects must match')
        o2 = Simple.objects.get(fedora_id=o1.fedora_id)
        self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')
        pass

    def test_query_by_string(self):
        o1 = Simple.objects.create(text='Hello world 1')
        time.sleep(5)
        o2 = Simple.objects.get(text='Hello world 1')
        self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertEqual(o1.id, o2.id, 'The id of the stored and retrieved objects must match')
        self.assertEqual(o1.fedora_id, o2.fedora_id, 'The fedora_id of the stored and retrieved objects must match')

    def test_query_by_and(self):
        objs = []
        for i in range(10):
            for j in range(10):
                objs.append(Complex.objects.create(a='%s' % i, b='%s' % j))
        time.sleep(5)
        for i in range(10):
            for j in range(10):
                objs_len = len(Complex.objects.filter(a='%s' % i, b='%s' % j))
                self.assertEqual(1, objs_len, 'Just 1 object expected')

        for i in range(10):
            objs = list(Complex.objects.filter(a='%s' % i))
            self.assertEqual(10, len(objs), 'Bad number of items retrieved from repository')
            self.assertEqual(set([x.b for x in objs]), set(['%s' % x for x in range(10)]), 'All elems are required')

        for i in range(10):
            objs = list(Complex.objects.filter(b='%s' % i))
            self.assertEqual(10, len(objs), 'Bad number of items retrieved from repository')
            self.assertEqual(set([x.a for x in objs]), set(['%s' % x for x in range(10)]), 'All elems are required')

        for i in range(10):
            for j in range(10):
                objs_len = len(Complex.objects.filter(Q(a='%s' % i) & Q(b='%s' % j)))
                self.assertEqual(1, objs_len, 'Just 1 object expected')

    def test_query_by_or(self):
        objs = []

        for i in range(4):
            for j in range(4):
                objs.append(Complex.objects.create(a='%s' % i, b='%s' % j))
        time.sleep(5)

        with connections['repository'].cursor() as cursor:
            es = cursor.cursor.connection.elasticsearch_connection.elasticsearch
            elasticsearch_index_name = cursor.cursor.connection.elasticsearch_connection.elasticsearch_index_name
            for i in range(4):
                for j in range(4):
                    query = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "type": {
                                            "value": "testapp_complex"
                                        }
                                    },
                                    {
                                        "bool": {
                                            "must": [
                                                {
                                                    "bool": {
                                                        "minimum_should_match": 1,
                                                        "should": [
                                                            {
                                                                "term": {
                                                                    "http_3a_2f_2fcesnet_2ecz_2fns_2frepository_23a": str(i)
                                                                }
                                                            },
                                                            {
                                                                "term": {
                                                                    "http_3a_2f_2fcesnet_2ecz_2fns_2frepository_23b": str(j)
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    }
                    scanner = elasticsearch.helpers.scan(
                        es,
                        query=query,
                        scroll=u'1m',
                        preserve_order=True,
                        index=elasticsearch_index_name,
                        from_=0)
                    count = 0
                    for r in scanner:
                        count += 1

                    search = es.search(
                        body=query,
                        index=elasticsearch_index_name,
                        size=100
                    )
                    search = search['hits']['hits']
                    search_count = len(search)
                    print("Search result", '\n'.join([str(x['_source']) for x in search]))
                    self.assertEqual(search_count, count, 'Scanner returned different number of results than search')
                    self.assertEqual(7, count, 'Scanner returned wrong number of documents')


        for i in range(4):
            for j in range(4):
                objs = list(Complex.objects.filter(Q(a='%s' % i) | Q(b='%s' % j)))
                for idx, o in enumerate(objs):
                    print(idx, o.a, o.b)
                objs_len = len(Complex.objects.filter(Q(a='%s' % i) | Q(b='%s' % j)))
                self.assertEqual(7, objs_len, '7 objects expected')

    def test_query_by_unmapped_property_name(self):
        obj = Complex.objects.create(a='1', b='1')
        time.sleep(5)
        objs = FedoraObject.objects.filter(**{
            CESNET.a : '1'
        })
        objs = list(objs)
        self.assertEqual(1, len(objs), 'Should have got only one object')
        self.assertEqual(str(objs[0].fedora_meta[CESNET.a][0]), obj.a)
        self.assertEqual(str(objs[0].fedora_meta[CESNET.b][0]), obj.b)
        self.assertEqual(objs[0].id, obj.id)
        self.assertIsInstance(obj.fedora_id, URIRef)
        self.assertIsInstance(objs[0].fedora_id, URIRef)
        self.assertEqual(objs[0].fedora_id, obj.fedora_id)
        self.assertTrue(objs[0].fedora_meta.from_search)

        obj2 = Complex.objects.get(fedora_id=obj.fedora_id)

        self.assertEqual(str(obj2.fedora_meta[CESNET.a][0]), obj.a)
        self.assertEqual(str(obj2.fedora_meta[CESNET.b][0]), obj.b)
        self.assertEqual(obj2.id, obj.id)
        self.assertEqual(obj2.fedora_id, obj.fedora_id)
        self.assertFalse(obj2.fedora_meta.from_search)
