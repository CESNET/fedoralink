import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import Simple
from fedoralink.tests.utils import FedoralinkTestBase
from fedoralink.authentication.as_user import as_admin


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestOrderBy(FedoralinkTestBase):
    """
    Test order_by in queries
    """

    def test_order_by(self):
        with as_admin():
            for i in range(10):
                Simple.objects.create(text='Hello %s' % i)

            for i, obj in enumerate(Simple.objects.all().order_by('text')):
                self.assertEqual('Hello %s' % i, obj.text)

            for i, obj in enumerate(Simple.objects.all().order_by('-text')):
                self.assertEqual('Hello %s' % (9-i), obj.text)

    def test_order_by_first(self):
        with as_admin():
            for i in range(10):
                Simple.objects.create(text='Hello %s' % i)

            obj = Simple.objects.all().first()
            self.assertIsNotNone(obj)
