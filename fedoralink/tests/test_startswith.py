import django
django.setup()

import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import InheritedA, Simple, InheritedB
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestStartsWith(FedoralinkTestBase):
    """
    Test __startswith, __istartswith on queries
    """

    def test_startswith(self):
        o1 = Simple.objects.create(text='abc')
        o2 = Simple.objects.create(text='def')

        # contains and icontains are the same for now as Elasticsearch does not have
        # a case insensitive wildcard search
        self.assertEqual(1, Simple.objects.filter(text__startswith='a').count())
        self.assertEqual(1, Simple.objects.filter(text__startswith='ab').count())
        self.assertEqual(0, Simple.objects.filter(text__startswith='b').count())
        self.assertEqual(0, Simple.objects.filter(text__startswith='c').count())

        self.assertEqual(1, Simple.objects.filter(text__istartswith='A').count())
        self.assertEqual(1, Simple.objects.filter(text__istartswith='aB').count())
        self.assertEqual(0, Simple.objects.filter(text__istartswith='B').count())
        self.assertEqual(0, Simple.objects.filter(text__istartswith='C').count())
