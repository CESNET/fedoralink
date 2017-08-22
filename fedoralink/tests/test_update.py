import django
from rdflib import Literal, XSD

django.setup()

import logging
import unittest.util

from fedoralink.fedorans import CESNET
from fedoralink.manager import ELASTICSEARCH
from fedoralink.models import FedoraObject
from fedoralink.tests.testserver.testapp.models import Complex
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestUpdate(FedoralinkTestBase):
    """
    Check that update operation (.save(), .update()) works and is propagated to Elasticsearch 
    """
    #
    def test_update(self):
        o1 = Complex.objects.create(a='1', b='2')
        o1.a = '3'
        o1.save()

        # check updated in the repository
        o2 = Complex.objects.get(pk=o1.pk)
        self.assertEqual(o1.a, o2.a, 'The text in the repository is not updated')
        self.assertEqual(o1.b, o2.b, 'b should not be changed')

        o3 = Complex.objects.via(ELASTICSEARCH).get(pk=o1.pk)
        self.assertEqual(o1.a, o3.a, 'The text in the elasticsearch is not updated')
        self.assertEqual(o1.b, o3.b, 'b should not be changed')

    def test_update_via_fedoraobject(self):
        o1 = Complex.objects.create(a='1', b='2')
        o1.a = '3'
        o1.save()

        FedoraObject.objects.filter(pk=o1.pk).update(**{CESNET.a : '5'})

        # check updated in the repository
        o2 = Complex.objects.get(pk=o1.pk)

        self.assertEqual('5', o2.a, 'The text in the repository is not updated')
        self.assertEqual('2', o2.b, 'b should not be changed')

        o3 = Complex.objects.via(ELASTICSEARCH).get(pk=o1.pk)
        self.assertEqual('5', o3.a, 'The text in the elasticsearch is not updated')
        self.assertEqual('2', o3.b, 'b should not be changed')
