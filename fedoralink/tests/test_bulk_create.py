import django
django.setup()

import logging
import unittest.util

from fedoralink.tests.utils import FedoralinkTestBase

from fedoralink.tests.testserver.testapp.models import Simple

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH = 2000


class TestBulkCreate(FedoralinkTestBase):
    """
    Test bulk creating objects
    """

    def test_bulk_create(self):
        a = Simple(text='Hello world 1')
        b = Simple(text='Hello world 2')

        Simple.objects.bulk_create([a, b])

        self.assertIsNotNone(a.id, 'Stored object must have an id')
        a = Simple.objects.get(id=a.id)
        self.assertIsNotNone(a.fedora_id, 'Stored object must have a fedora_id')
        self.assertEqual(a.text, 'Hello world 1')

        self.assertIsNotNone(b.id, 'Stored object must have an id')
        b = Simple.objects.get(id=b.id)
        self.assertIsNotNone(b.fedora_id, 'Stored object must have a fedora_id')
        self.assertEqual(b.text, 'Hello world 2')
