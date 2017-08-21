import re
import time
import traceback

from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase

import fedoralink.models
from fedoralink.authentication.as_user import as_admin
from fedoralink.db.delegated_requests import delete
from fedoralink.db.queries import InsertQuery
from fedoralink.manager import FEDORA_REPOSITORY
from fedoralink.models import FedoraObject


class FedoraTestBase(TransactionTestCase):
    def setUp(self):
        try:
            # try to get the root object. If found, delete the root and wait a bit so that elasticsearch catches
            FedoraObject.objects.via(FEDORA_REPOSITORY).get(fedora_id='')
            self.tearDown()
            time.sleep(1)
        except FedoraObject.DoesNotExist:
            pass
        except:
            traceback.print_exc()
        prefix = connections['repository'].get_connection_params()['options']['namespace'].prefix
        with connections['repository'].cursor() as cursor:
            with as_admin():
                cursor.execute(InsertQuery(
                    [
                        {
                            'parent': '/fcrepo/rest',  # break out of the test-test context
                            'bitstream': None,
                            'doc_type': None,
                            'fields': {
                            },
                            'slug': prefix,
                            'options': None
                        }
                    ]
                ))
                print(cursor)
        call_command('migrate', '--database', 'repository', 'fedoralink')
        self.maxDiff = None
        time.sleep(1)

    def __delete(self, fc, url):
        auth = fc._get_auth()
        delete(url, auth=auth)
        tombstone_url = url
        if not tombstone_url.endswith('/'):
            tombstone_url += '/'
        tombstone_url += 'fcr:tombstone'
        delete(tombstone_url, auth=auth)

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
                        subjects.add(str(meta[0]))

                for subject in subjects:
                    if not same_urls(subject, rurl):
                        self.__delete(fc, subject)

                self.assertEqual(len(subjects), 1)


class FedoralinkTestBase(FedoraTestBase):
    def setUp(self):
        super().setUp()
        call_command('migrate', '--database', 'repository', 'testapp')
        time.sleep(1)


def same_urls(a, b):
    if a.endswith('/'):
        a = a[:-1]
    if b.endswith('/'):
        b = b[:-1]
    return a == b

