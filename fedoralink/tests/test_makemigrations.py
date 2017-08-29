import django
from django.core.management import call_command
from rdflib import Literal, XSD

django.setup()

import logging
import unittest.util

from fedoralink.fedorans import CESNET
from fedoralink.manager import ELASTICSEARCH
from fedoralink.models import FedoraObject
from fedoralink.tests.testserver.testapp.models import Complex
from fedoralink.tests.utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH=2000


class TestMakeMigrations(FedoralinkTestBase):
    """
    Calls makemigrations
    """
    #
    def test_makemigrations(self):
        call_command('makemigrations', 'testapp')
        call_command('migrate', '--database', 'repository', 'testapp')