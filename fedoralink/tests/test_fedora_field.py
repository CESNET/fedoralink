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
from fedoralink.tests.testserver.testapp.models import Simple, Complex, ArrayFieldModel
from .utils import FedoraTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestFedoraFieldFetch(FedoraTestBase):
    """
    Test storing objects and searching them by string properties
    """

    def test_simple_store_fetch(self):
        o1 = ArrayFieldModel.objects.create(a=['Hello world 1'])
        self.assertIsNotNone(o1.id, 'Stored object must have an id')
        self.assertIsNotNone(o1.fedora_id, 'Stored object must have a fedora_id')
        self.assertNotEqual(o1.fedora_id, '')
        self.assertEqual(o1.id, url2id(o1.fedora_id), 'The id of the stored and retrieved objects must match')
        o2 = ArrayFieldModel.objects.get(fedora_id=o1.fedora_id)
        self.assertEqual(o1.a, o2.a, 'The text of the stored and retrieved objects must match')

    def test_search_in(self):
        o1 = ArrayFieldModel.objects.create(a=['Hello', 'World'])
        lst = list(ArrayFieldModel.objects.filter(a__in=['Hello']))
        self.assertEqual(len(lst), 1)