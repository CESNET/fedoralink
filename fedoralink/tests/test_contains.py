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
        o1 = Simple.objects.create(text='a')
        self.assertEqual(1, Simple.objects.filter(text__contains='a').count())
