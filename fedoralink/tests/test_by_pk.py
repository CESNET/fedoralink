import unittest.util

import elasticsearch.helpers
import time
from django.core.management import call_command
from django.db import connections
from django.db.models import Q, F, Value, CharField
from django.test import TransactionTestCase
from rdflib import URIRef

from fedoralink.db.queries import InsertQuery

import logging

from fedoralink.fedorans import CESNET
from fedoralink.idmapping import url2id
from fedoralink.models import FedoraObject
from fedoralink.tests.testserver.testapp.models import Simple, Complex

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestByPk(TransactionTestCase):
    def setUp(self):
        with connections['repository'].cursor() as cursor:
            cursor.execute(InsertQuery(
                [
                    {
                        'parent': '/rest',  # break out of the test-test context
                        'doc_type': None,
                        'fields': {
                        },
                        'slug': 'test-test'
                    }
                ]
            ))
            print(cursor)
        call_command('migrate', '--database', 'repository', 'testapp')
        self.maxDiff = None

        self.object = Simple.objects.create(text='Hello world 1')
        self.assertIsNotNone(self.object.id, 'Stored object must have an id')
        self.assertIsNotNone(self.object.fedora_id, 'Stored object must have a fedora_id')

    def test_fedora_id(self):
        o2 = Simple.objects.get(fedora_id=self.object.fedora_id)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')

    def test_pk(self):
        o2 = Simple.objects.get(pk=self.object.fedora_id)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')

    def test_integer_pk(self):
        o2 = Simple.objects.get(pk=self.object.pk)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')

