import datetime
import logging
import unittest.util
from uuid import UUID

from dateutil.tz import tzlocal
from decimal import Decimal

from fedoralink.manager import ELASTICSEARCH
from fedoralink.tests.testserver.testapp.models import BasicFieldTypes
from .utils import FedoralinkTestBase

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('elasticsearch.trace').propagate = True

unittest.util._MAX_LENGTH = 2000


class TestBasicFieldTypes(FedoralinkTestBase):
    """
    Check that update operation (.save(), .update()) works and is propagated to Elasticsearch 
    """

    def test_create_basic_field_types(self):
        o1 = self._create()
        o1.save()

        # check updated in the repository
        o2 = BasicFieldTypes.objects.get(pk=o1.pk)
        self._assert_django_model_equals(o1, o2)

    def test_create_null_bool(self):
        o1 = self._create(null_boolean=None)
        o1.save()

        # check updated in the repository
        o2 = BasicFieldTypes.objects.get(pk=o1.pk)
        self._assert_django_model_equals(o1, o2)

    def test_from_elasticsearch(self):
        o1 = self._create()
        o1.save()

        # check updated in the repository
        o2 = BasicFieldTypes.objects.via(ELASTICSEARCH).get(pk=o1.pk)
        self._assert_django_model_equals(o1, o2)


    def test_null_bool_from_elasticsearch(self):
        o1 = self._create(null_boolean=None)
        o1.save()

        # check updated in the repository
        o2 = BasicFieldTypes.objects.via(ELASTICSEARCH).get(pk=o1.pk)
        self._assert_django_model_equals(o1, o2)


    def _assert_django_model_equals(self, o1, o2):
        for fld in o1._meta.fields:
            self.assertEqual(getattr(o1, fld.name), getattr(o2, fld.name), 'Error comparing attr %s' % fld)

    @staticmethod
    def _create(**kwargs):
        defaults = {'char_field': 'char', 'text_field': 'text', 'slug_field': '/text/blah',
                    'url_field': 'http://localhost/text/blah', 'uuid_field': UUID('{2d93325e-dc76-4ae4-b9fd-bd1e10c0d784}'),
                    'int_field': 123, 'biginteger_field': 123123123123, 'positive_integer_field': 123123123,
                    'positive_small_integer_field': 123, 'small_integer_field': -123, 'float_field': 12.24,
                    'decimal_field': Decimal('12.24'), 'date_field': datetime.datetime.now(tzlocal()).date(),
                    'time_field': datetime.time(hour=12, minute=25, second=20, microsecond=234000),
                    'datetime_field': datetime.datetime.now(tzlocal()), 'duration_field': datetime.timedelta(days=1),
                    'ip_field': '123.123.123.123', 'email': 'miroslav.simek@vscht.cz', 'boolean_field': True,
                    'null_boolean': False}
        defaults.update(kwargs)
        return BasicFieldTypes.objects.create(
            **defaults
        )
