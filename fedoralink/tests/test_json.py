import django

from fedoralink.manager import ELASTICSEARCH

django.setup()

import logging
import unittest.util
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from fedoralink.tests.testserver.testapp.models import BinaryFieldTypes, JsonModel
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestJson(FedoralinkTestBase):
    """
    Test storing and retrieving json fields
    """

    def test_json(self):
        o = JsonModel.objects.create(json_single={'a': 1})

        o2 = JsonModel.objects.get(fedora_id=o.fedora_id)
        self.assertDictEqual(o.json_single, o2.json_single)

        o2 = JsonModel.objects.via(ELASTICSEARCH).get(fedora_id=o.fedora_id)
        self.assertDictEqual(o.json_single, o2.json_single)

        o.json_single = {'b': 1}
        o.save()

        o2 = JsonModel.objects.get(fedora_id=o.fedora_id)
        self.assertDictEqual(o.json_single, o2.json_single)

        o.json_multiple = [
            {'a': 1},
            {'b': 2}
        ]
        o.save()

        o2 = JsonModel.objects.get(fedora_id=o.fedora_id)
        self.assertDictEqual(o.json_multiple[0], o2.json_multiple[0])
        self.assertDictEqual(o.json_multiple[1], o2.json_multiple[1])

