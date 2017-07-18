import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import Simple
from fedoralink.tests.utils import FedoraTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestQueryAggregations(FedoraTestBase):
    """
    Test aggregation methods in queries 
    """

    def test_count_objects(self):
        Simple.objects.create(text='Hello')
        Simple.objects.create(text='Hello')
        Simple.objects.create(text='Hello')
        Simple.objects.create(text='World')

        cnt = Simple.objects.count()
        self.assertEqual(4, cnt)

        cnt = Simple.objects.filter(text='Hello').count()
        self.assertEqual(3, cnt)

