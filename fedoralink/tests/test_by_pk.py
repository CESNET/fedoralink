import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import Simple
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestByPk(FedoralinkTestBase):
    """
    Test access to fedora resources via url(fedora standard) or integer(django standard) pk 
    """
    def setUp(self):
        super().setUp()

        self.object = Simple.objects.create(text='Hello world 1')
        self.assertIsNotNone(self.object.id, 'Stored object must have an id')
        self.assertIsNotNone(self.object.fedora_id, 'Stored object must have a fedora_id')

    def test_fedora_id(self):
        o2 = Simple.objects.get(fedora_id=self.object.fedora_id)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertFalse(o2.fedora_meta.from_search)

    def test_pk(self):
        o2 = Simple.objects.get(pk=self.object.fedora_id)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertFalse(o2.fedora_meta.from_search)

    def test_integer_pk(self):
        o2 = Simple.objects.get(pk=self.object.pk)
        self.assertEqual(self.object.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertFalse(o2.fedora_meta.from_search)

