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
