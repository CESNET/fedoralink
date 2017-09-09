import django
django.setup()

import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import InheritedA, Simple, InheritedB
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestInheritance(FedoralinkTestBase):
    """
    Test storing, fetching and searching inherited objects
    """

    def test_save_fetch_inherited(self):
        o1 = InheritedA.objects.create(text='Hello world 1', a='a')
        self.assertIsNotNone(o1.id, 'Stored object must have an id')
        self.assertIsNotNone(o1.fedora_id, 'Stored object must have a fedora_id')

        o2 = InheritedA.objects.get(fedora_id=o1.fedora_id)
        self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')
        self.assertEqual(o1.a, o2.a, 'The a field of the stored and retrieved objects must match')

        self.assertTrue(isinstance(o2, InheritedA), 'Must be instance of the inherited class')
        self.assertTrue(isinstance(o2, Simple), 'Must be instance of the parent class')

        o2 = Simple.objects.get(fedora_id=o1.fedora_id)
        self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')

        count = 0
        for o2 in InheritedA.objects.all():
            self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')
            self.assertEqual(o1.a, o2.a, 'The a field of the stored and retrieved objects must match')
            count += 1

        self.assertEqual(count, 1, 'Expecting 1 object from .all')

        count = 0
        for o2 in Simple.objects.all():
            self.assertEqual(o1.text, o2.text, 'The text of the stored and retrieved objects must match')
            count += 1

        self.assertEqual(count, 1, 'Expecting 1 object from .all')

        self.assertEqual(1, InheritedA.objects.count(), 'There should be one object present')
        self.assertEqual(1, Simple.objects.count(), 'There should be one object present')


        self.assertEqual(0, InheritedB.objects.count(), 'There should be no InheritedB object present')

