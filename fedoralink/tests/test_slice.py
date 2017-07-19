import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import Simple
from fedoralink.tests.utils import FedoraTestBase
from fedoralink.authentication.as_user import as_admin


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestSlice(FedoraTestBase):
    """
    Test slice (pagination) in queries
    """

    def test_slice(self):
        with as_admin():
            for i in range(10):
                Simple.objects.create(text='Hello %s' % i)

            for sl in range(2, 10, 2):
                objs = list(Simple.objects.all()[sl:sl+2])
                self.assertEqual(len(objs), 2, 'Must return slice with two elems')

    def test_ordered_slice(self):
        with as_admin():
            for i in range(10):
                Simple.objects.create(text='Hello %s' % i)

            for sl in range(0, 10, 2):
                objs = list(Simple.objects.all().order_by('text')[sl:sl+2])
                self.assertEqual(len(objs), 2, 'Must return slice with two elems')
                self.assertEqual(objs[0].text, 'Hello %s' % sl)
                self.assertEqual(objs[1].text, 'Hello %s' % (sl+1))