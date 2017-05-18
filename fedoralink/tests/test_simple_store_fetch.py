from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase

from fedoralink.db.queries import InsertQuery

import logging

from fedoralink.idmapping import url2id
from fedoralink.models import FedoraObject
from fedoralink.tests.testserver.testapp.models import Simple

logging.basicConfig(level=logging.DEBUG)

class TestSimpleStoreFetch(TransactionTestCase):
    def setUp(self):
        with connections['repository'].cursor() as cursor:
            cursor.execute(InsertQuery(
                [
                    {
                        'parent': '/rest',       # break out of the test-test context
                        'doc_type': None,
                        'fields': {
                        },
                        'slug': 'test-test'
                    }
                ]
            ))
            print(cursor)
        call_command('migrate', '--database', 'repository', 'testapp')

    def test_simple_store_fetch(self):
        o1 = Simple.objects.create(text='Hello world 1')
        self.assertIsNotNone(o1.id, 'Stored object must have an id')
        self.assertIsNotNone(o1.fedora_id, 'Stored object must have a fedora_id')
        self.assertEqual(o1.id, url2id(o1.fedora_id), 'The id of the stored and retrieved objects must match')
        o2 = Simple.objects.get(fedora_id=o1.fedora_id)
        self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')
        pass
