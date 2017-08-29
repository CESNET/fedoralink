import django
django.setup()

from fedoralink.tests.utils import FedoralinkTestBase


import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import Simple, ModelWithForeignKey, ModelWithForeignKeyArray

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestForeignArray(FedoralinkTestBase):
    """
    Test storing objects referencing array of other objects
    """

    def test_foreign_array(self):
        a1 = Simple.objects.create(text='abc')
        a2 = Simple.objects.create(text='def')

        b = ModelWithForeignKeyArray(f=[a1,a2])
        b.save()

        self.assertTrue(a1.id in [x.id for x in b.f])
        self.assertTrue(a1.fedora_id in [x.fedora_id for x in b.f])

        c = ModelWithForeignKeyArray.objects.get(id=b.id)

        self.assertTrue(a1.id in [x.id for x in c.f])
        self.assertTrue(a1.fedora_id in [x.fedora_id for x in c.f])

    def test_foreign_array_update_from_empty(self):
        a1 = Simple.objects.create(text='abc')
        a2 = Simple.objects.create(text='def')

        b = ModelWithForeignKeyArray()
        b.save()

        b.f = [a1, a2]
        b.save()

        self.assertTrue(a1.id in [x.id for x in b.f])
        self.assertTrue(a1.fedora_id in [x.fedora_id for x in b.f])

        self.assertTrue(a2.id in [x.id for x in b.f])
        self.assertTrue(a2.fedora_id in [x.fedora_id for x in b.f])

        c = ModelWithForeignKeyArray.objects.get(id=b.id)

        self.assertTrue(a1.id in [x.id for x in c.f])
        self.assertTrue(a1.fedora_id in [x.fedora_id for x in c.f])

        self.assertTrue(a2.id in [x.id for x in c.f])
        self.assertTrue(a2.fedora_id in [x.fedora_id for x in c.f])


    def test_foreign_array_update_from_another(self):
        a1 = Simple.objects.create(text='abc')
        a2 = Simple.objects.create(text='def')

        b = ModelWithForeignKeyArray(f=[a1])
        b.save()

        self.assertTrue(a1.id in [x.id for x in b.f])
        self.assertTrue(a1.fedora_id in [x.fedora_id for x in b.f])

        self.assertFalse(a2.id in [x.id for x in b.f])
        self.assertFalse(a2.fedora_id in [x.fedora_id for x in b.f])

        b.f = [a2]
        b.save()

        c = ModelWithForeignKeyArray.objects.get(id=b.id)

        self.assertFalse(a1.id in [x.id for x in c.f])
        self.assertFalse(a1.fedora_id in [x.fedora_id for x in c.f])

        self.assertTrue(a2.id in [x.id for x in c.f])
        self.assertTrue(a2.fedora_id in [x.fedora_id for x in c.f])
