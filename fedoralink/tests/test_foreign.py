import django
django.setup()

from fedoralink.tests.utils import FedoralinkTestBase


import logging
import unittest.util
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from fedoralink.tests.testserver.testapp.models import BinaryFieldTypes, Simple, ModelWithForeignKey

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestForeign(FedoralinkTestBase):
    """
    Test storing objects referencing to other objects
    """

    def test_foreign(self):
        a = Simple.objects.create(text='abc')
        b = ModelWithForeignKey(f=a)
        b.save()

        self.assertEqual(a.id, b.f_id)

        bb = ModelWithForeignKey.objects.get(fedora_id=b.fedora_id)
        self.assertEqual(bb.f_id, a.id)

    def test_foreign_update(self):
        a = Simple.objects.create(text='abc')
        c = Simple.objects.create(text='test1')

        b = ModelWithForeignKey(f=a)
        b.save()

        b.f = c
        b.save()

        bb = ModelWithForeignKey.objects.get(fedora_id=b.fedora_id)
        self.assertEqual(bb.f_id, c.id)
