import logging
import time
import unittest.util

from fedoralink.manager import ELASTICSEARCH
from fedoralink.tests.testserver.testapp.models import Simple
from .utils import FedoraTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestPkViaElasticsearch(FedoraTestBase):
    """
    Check that Elasticsearch could be used for finding fedora objects by their urls
    """
    def setUp(self):
        super().setUp()

        self.object = Simple.objects.create(text='Hello world 1')
        self.assertIsNotNone(self.object.id, 'Stored object must have an id')
        self.assertIsNotNone(self.object.fedora_id, 'Stored object must have a fedora_id')
        time.sleep(5)

    def test_fedora_id(self):
        o2 = Simple.objects.via(ELASTICSEARCH).get(fedora_id=self.object.fedora_id)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertTrue(o2.fedora_meta.from_search)

    def test_pk(self):
        o2 = Simple.objects.via(ELASTICSEARCH).get(pk=self.object.fedora_id)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertTrue(o2.fedora_meta.from_search)

    def test_integer_pk(self):
        o2 = Simple.objects.via(ELASTICSEARCH).get(pk=self.object.pk)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertTrue(o2.fedora_meta.from_search)

