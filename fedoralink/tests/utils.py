import time
from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase

from fedoralink.db.queries import InsertQuery
from fedoralink.models import FedoraObject


class FedoraTestBase(TransactionTestCase):
    def setUp(self):
        try:
            # try to get the root object. If found, delete the root and wait a bit so that elasticsearch catches
            FedoraObject.objects.get(fedora_id='')
            self.tearDown()
            time.sleep(5)
        except:
            pass

        with connections['repository'].cursor() as cursor:
            cursor.execute(InsertQuery(
                [
                    {
                        'parent': '/rest',  # break out of the test-test context
                        'doc_type': None,
                        'fields': {
                        },
                        'slug': 'test-test'
                    }
                ]
            ))
            print(cursor)
        call_command('migrate', '--database', 'repository', 'testapp')
        self.maxDiff = None
        time.sleep(3)

    def tearDown(self):
        for conn in connections.databases:
            with connections[conn].cursor() as cursor:
                try:
                    cursor.cursor.connection.delete_all_data()
                except:
                    pass
        time.sleep(3)