import django
from rdflib.namespace import DC

from fedoralink.fedorans import ACL, RDF

django.setup()

from fedoralink.models import FedoraObject
import logging
import unittest.util

from fedoralink.tests.testserver.testapp.models import DifferentNamespace
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH = 2000


class TestDifferentNamespace(FedoralinkTestBase):
    """
    Test storing and retrieving models with fields in different rdf namespace than the class
    """

    def test_different_namespace(self):
        o = DifferentNamespace.objects.create(
            a='a',
            b='b'
        )

        o2 = FedoraObject.objects.get(fedora_id=o.fedora_id)
        meta = o2.fedora_meta

        # check fields are in the correct namespaces
        self.assertEqual(str(meta[ACL.a][0]), 'a')
        self.assertEqual(str(meta[DC.b][0]), 'b')

        # check class has the correct rdf type
        rdf_types = meta[RDF.type]
        self.assertIn(ACL.Authorization, rdf_types)