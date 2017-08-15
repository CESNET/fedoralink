import logging
import unittest.util
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from fedoralink.idmapping import url2id
from fedoralink.tests.testserver.testapp.models import Simple, BinaryFieldTypes
from .utils import FedoraTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestBinary(FedoraTestBase):
    """
    Test storing objects and searching them by string properties
    """

    def test_binary(self):
        image_stream = BytesIO()
        img = Image.new('RGB', (1,1))
        img.save(image_stream, format='PNG')

        o1 = BinaryFieldTypes(
            binary_field=b'Hello world',
            file=SimpleUploadedFile('file.txt', b'File', 'text/plain'),
            image=SimpleUploadedFile('image.png', image_stream.getvalue(), 'image/png')
        )

        o1.save()

        o2 = BinaryFieldTypes.objects.get(pk=o1.pk)

        self.assertEqual(o2.binary_field, o1.binary_field)
        self.assertEqual(self._read_chunks(o2.file), b'File')
        self.assertEqual(self._read_chunks(o2.image), image_stream.getvalue())

        o2.file = SimpleUploadedFile('file.txt', b'File 2', 'text/plain')
        o2.save()

        o3 = BinaryFieldTypes.objects.get(pk=o1.pk)
        self.assertEqual(self._read_chunks(o3.file), b'File 2')

    @staticmethod
    def _read_chunks(data):
        data = [x for x in data.chunks()]
        return b''.join(data)
