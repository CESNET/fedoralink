import django
django.setup()

import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import InheritedA, Simple, InheritedB
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestContains(FedoralinkTestBase):
    """
    Test __contains on queries
    """

    def test_contains(self):
        o1 = Simple.objects.create(text='abc')
        o2 = Simple.objects.create(text='def')

        # contains and icontains are the same for now as Elasticsearch does not have
        # a case insensitive wildcard search
        self.assertEqual(1, Simple.objects.filter(text__contains='a').count())
        self.assertEqual(1, Simple.objects.filter(text__contains='b').count())
        self.assertEqual(1, Simple.objects.filter(text__contains='c').count())

        # but icontains at first converts its argument to lowercase so if the data entered
        # to Keyword type are lowercase, upper case in search will work
        self.assertEqual(1, Simple.objects.filter(text__icontains='A').count())
        self.assertEqual(1, Simple.objects.filter(text__icontains='B').count())
        self.assertEqual(1, Simple.objects.filter(text__icontains='C').count())

        o3 = Simple.objects.create(text='abb')
        self.assertEqual(2, Simple.objects.filter(text__contains='a').count())
        self.assertEqual(2, Simple.objects.filter(text__contains='b').count())
        self.assertEqual(1, Simple.objects.filter(text__contains='c').count())
