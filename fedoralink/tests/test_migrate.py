import logging

from fedoralink.models import FedoraObject
from .utils import FedoraTestBase

logging.basicConfig(level=logging.DEBUG)


class TestMigrate(FedoraTestBase):
    def test_migration(self):
        migrations = FedoraObject.objects.get(fedora_id='django_migrations')
        simple = FedoraObject.objects.get(fedora_id='testapp_simple')
