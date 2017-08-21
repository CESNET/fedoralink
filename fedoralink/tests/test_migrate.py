import logging

from fedoralink.models import FedoraObject
from .utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)


class TestMigrate(FedoralinkTestBase):
    """
    Try to apply migrations of sample fedora models
    """
    def test_migration(self):
        migrations = FedoraObject.objects.get(fedora_id='django_migrations')
        simple = FedoraObject.objects.get(fedora_id='testapp_simple')
