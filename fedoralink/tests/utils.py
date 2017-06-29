import time

import re
from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase

from fedoralink.authentication.as_user import as_admin
from fedoralink.db.queries import InsertQuery
from fedoralink.models import FedoraObject


class FedoraTestBase(TransactionTestCase):
    def setUp(self):
        try:
            # try to get the root object. If found, delete the root and wait a bit so that elasticsearch catches
            FedoraObject.objects.get(fedora_id='')
            self.tearDown()
            time.sleep(1)
        except:
            pass
        with connections['repository'].cursor() as cursor:
            with as_admin():
                cursor.execute(InsertQuery(
                    [
                        {
                            'parent': '/fcrepo/rest',  # break out of the test-test context
                            'doc_type': None,
                            'fields': {
                            },
                            'slug': 'test-test',
                            'options': None
                        }
                    ]
                ))
                print(cursor)
        call_command('migrate', '--database', 'repository', 'testapp')
        self.maxDiff = None
        time.sleep(1)

    def tearDown(self):
        for conn in connections.databases:
            with connections[conn].cursor() as cursor:
                try:
                    with as_admin():
                        cursor.cursor.connection.delete_all_data()
                except:
                    pass
        time.sleep(1)
        # check if there are any other resources in the root - if so, something went wrong
        with connections['repository'].cursor() as cursor:
            with as_admin():
                fc = cursor.cursor.connection.fedora_connection
                rurl = fc.repo_url
                rurl = re.sub(r'rest/.*', 'rest', rurl)
                data = fc.get_object(rurl, fetch_child_metadata=True)
                subjects = set()
                for d in data:
                    for meta in d.rdf_metadata:
                        subjects.add(meta[0])
                self.assertEqual(len(subjects), 1)