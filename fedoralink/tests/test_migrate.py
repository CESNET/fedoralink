from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase

from fedoralink.db.queries import InsertQuery

import logging

from fedoralink.models import FedoraObject

logging.basicConfig(level=logging.DEBUG)

class TestMigrate(TransactionTestCase):
    def test_migration(self):
        with connections['repository'].cursor() as cursor:
            cursor.execute(InsertQuery(
                [
                    {
                        'parent': '/rest',       # break out of the test-test context
                        'doc_type': None,
                        'fields': {
                        },
                        'slug': 'test-test'
                    }
                ]
            ))
            print(cursor)
        call_command('migrate', '--database', 'repository', 'testapp')
        migrations = FedoraObject.objects.get(fedora_id='django_migrations')
        simple = FedoraObject.objects.get(fedora_id='testapp_simple')
        print("All ok ...")
