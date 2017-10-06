import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import Simple, ModelWithForeignKey
from fedoralink.tests.utils import FedoralinkTestBase
from fedoralink.authentication.as_user import as_admin


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestQueryPredicates(FedoralinkTestBase):
    """
    Test query predicates
    """

    def test_isnull(self):
        with as_admin():
            a = Simple.objects.create(text='Not Null')
            b = ModelWithForeignKey.objects.create(f=a)
            c = ModelWithForeignKey.objects.create()
            d = ModelWithForeignKey.objects.create()

            self.assertEqual(ModelWithForeignKey.objects.filter(f__isnull=True).count(), 2)
            self.assertEqual(ModelWithForeignKey.objects.filter(f=None).count(), 2)
            self.assertEqual(ModelWithForeignKey.objects.filter(f__isnull=False).count(), 1)

