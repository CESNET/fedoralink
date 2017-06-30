import logging
import time
import unittest.util

import elasticsearch.helpers
from django.db import connections
from django.db.models import Q
from rdflib import URIRef

from fedoralink.authentication.as_user import as_admin
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
        with as_admin():
            o1 = ArrayFieldModel.objects.create(a=['Hello world 1'])
            self.assertIsNotNone(o1.id, 'Stored object must have an id')
            self.assertIsNotNone(o1.fedora_id, 'Stored object must have a fedora_id')
            self.assertNotEqual(o1.fedora_id, '')
            self.assertEqual(o1.id, url2id(o1.fedora_id), 'The id of the stored and retrieved objects must match')
            o2 = ArrayFieldModel.objects.get(fedora_id=o1.fedora_id)
            self.assertEqual(o1.a, o2.a, 'The text of the stored and retrieved objects must match')

    def test_search_in(self):
        with as_admin():
            o1 = ArrayFieldModel.objects.create(a=['Hello', 'World'])
            lst = list(ArrayFieldModel.objects.filter(a__in=['Hello']))
            self.assertEqual(len(lst), 1)

    def test_search_in2(self):
        with as_admin():
            Simple.objects.create(text='Hello')
            Simple.objects.create(text='World')
            Simple.objects.create(text='blah')

            lst = list(Simple.objects.filter(text__in=['Hello', 'World']))
            self.assertEqual(len(lst), 2)

            lst = set([ x.text for x in lst])
            self.assertEqual(lst, {'Hello', 'World'})
