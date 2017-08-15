from __future__ import unicode_literals

import datetime
import logging
from uuid import UUID

import decimal

import iso8601
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.base.validation import BaseDatabaseValidation
from django import VERSION as django_version
from django.db import models

from fedoralink.db import FedoraError
from fedoralink.db.connection import FedoraWithElasticConnection
from fedoralink.db.cursor import DatabaseCursor
from fedoralink.db.lookups import Operation

log = logging.getLogger(__file__)

try:
    from django.db.backends import BaseDatabaseClient
except ImportError:
    from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    def runshell(self):
        raise NotImplementedError("Running database shell is not supported")


class DatabaseCreation(BaseDatabaseCreation):
    def _clone_test_db(self, number, verbosity, keepdb=False):
        raise Exception("Not implemented")

    def create_test_db(self, *args, **kwargs):
        settings = self.connection.settings_dict
        namespace_options = settings.setdefault('CONNECTION_OPTIONS', {'namespace': {}})['namespace']
        namespace_options['namespace'] = '%s-%s' % (namespace_options.get('namespace'), 'test')
        namespace_options['prefix'] = '%s-%s' % (namespace_options.get('prefix'), 'test')

    def destroy_test_db(self, *args, **kwargs):
        if not self.connection.connection:
            # force create connection
            self.connection.cursor()
        self.connection.connection.delete_all_data()


class DatabaseFeatures(BaseDatabaseFeatures):
    can_return_ids_from_bulk_insert = True
    can_return_id_from_insert = True
    supports_transactions = False
    pass


class DatabaseIntrospection(BaseDatabaseIntrospection):
    def get_indexes(self, cursor, table_name):
        return {}

    def get_constraints(self, cursor, table_name):
        return {}

    def get_key_columns(self, cursor, table_name):
        return []

    def get_table_list(self, cursor):
        return []


class IdentityCast(object):
    def __mod__(self, other):
        return other


class ConstructorCast(object):
    def __init__(self, clz):
        self.clz = clz

    def __mod__(self, other):
        return self.clz(other)


class NotCast(object):
    def __mod__(self, other):
        return Operation('not', other)


class FedoraDatabaseOperations(BaseDatabaseOperations):
    compiler_module = "fedoralink.db.compiler"

    def quote_name(self, name):
        return name

    def no_limit_value(self):
        return -1

    # do not transform datetime to string, just return the datetime - both fedora and elastic can handle it
    def adapt_datetimefield_value(self, value):
        return value

    def field_cast_sql(self, db_type, internal_type):
        return IdentityCast()

    def lookup_cast(self, lookup_type, internal_type=None):
        return IdentityCast()

    def logical_binary_operation_delimiter_sql(self):
        return ConstructorCast(Operation)

    def logical_not_operation_delimiter_sql(self):
        return NotCast()

    def logical_group_delimiter_sql(self):
        return IdentityCast()

    def combine_expression(self, connector, sub_expressions):
        """Combine a list of subexpressions into a single expression, using
        the provided connecting operator. This is required because operators
        can vary between backends (e.g., Oracle with %% and &) and between
        subexpression types (e.g., date expressions)
        """
        return Operation(connector, *sub_expressions)

    def get_db_converters(self, expression):
        converters = super(FedoraDatabaseOperations, self).get_db_converters(expression)
        field = expression.output_field
        print(field, type(field))
        if isinstance(field, models.UUIDField):
            converters += [self.convert_uuid]
        if isinstance(field, models.DecimalField):
            converters += [self.convert_decimal]
        if isinstance(field, models.DateTimeField):
            converters += [self.convert_datetime]
        if isinstance(field, models.TimeField):
            converters += [self.convert_time]
        if isinstance(field, models.DateField):
            converters += [self.convert_date]
        if isinstance(field, models.FileField):
            converters += [self.convert_file]
        return converters

    def convert_uuid(self, value, expression, connection, context):
        if value is not None and isinstance(value, str):
            value = UUID(value)
        return value

    def convert_decimal(self, value, expression, connection, context):
        if value is not None and isinstance(value, str):
            value = decimal.Decimal(value)
        return value

    def convert_date(self, value, expression, connection, context):
        if value is not None and isinstance(value, str):
            value = iso8601.parse_date(value).date()
        return value

    def convert_time(self, value, expression, connection, context):
        if value is not None and isinstance(value, str):
            value = datetime.datetime.strptime(value, "%H:%M:%S.%f").time()
        return value

    def convert_datetime(self, value, expression, connection, context):
        if value is not None and isinstance(value, str):
            value = iso8601.parse_date(value)
        return value

    def convert_file(self, value, expression, connection, context):
        raise NotImplementedError()


class DatabaseValidation(BaseDatabaseValidation):
    pass


class FedoraDatabase(object):
    # Base class for all exceptions
    Error = FedoraError

    class Binary():
        def __init__(self, value):
            self.value = value

    class DatabaseError(FedoraError):
        """Database-side errors."""

    class OperationalError(
        DatabaseError,
    ):
        """Exceptions related to the database operations, out of the programmer control."""

    class IntegrityError(
        DatabaseError,
    ):
        """Exceptions related to database Integrity."""

    class DataError(
        DatabaseError,
    ):
        """Exceptions related to invalid data"""

    class InterfaceError(
        Error,
    ):
        """Exceptions related to the pyldap interface."""

    class InternalError(
        DatabaseError,
    ):
        """Exceptions encountered within the database."""

    class ProgrammingError(
        DatabaseError,
    ):
        """Invalid data send by the programmer."""

    class NotSupportedError(
        DatabaseError,
    ):
        """Exception for unsupported actions."""


class FedoraSchemaEditor(BaseDatabaseSchemaEditor):
    def quote_value(self, value):
        pass

    def prepare_default(self, value):
        raise Exception("Should not be called")

    def create_model(self, model):
        with self.connection.cursor() as cursor:
            cursor.connection.create_model(model)


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'fedoralink'

    Database = FedoraDatabase
    SchemaEditorClass = FedoraSchemaEditor

    operators = {
        'exact': '= %s',
        'iexact': 'LIKE %s',
        'contains': 'LIKE BINARY %s',
        'icontains': 'LIKE %s',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE BINARY %s',
        'endswith': 'LIKE BINARY %s',
        'istartswith': 'LIKE %s',
        'iendswith': 'LIKE %s',
    }

    client_class = DatabaseClient
    creation_class = DatabaseCreation
    features_class = DatabaseFeatures
    introspection_class = DatabaseIntrospection
    validation_class = DatabaseValidation
    ops_class = FedoraDatabaseOperations

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        if django_version[:2] < (1, 11):
            self.ops = FedoraDatabaseOperations(self)
            self.client = DatabaseClient(self)
            self.features = DatabaseFeatures(self)
            self.creation = DatabaseCreation(self)
            self.introspection = DatabaseIntrospection(self)
            self.validation = DatabaseValidation(self)

        self.settings_dict['SUPPORTS_TRANSACTIONS'] = True
        self.autocommit = True
        self.page_size = 100

    def close(self):
        if hasattr(self, 'validate_thread_sharing'):
            # django >= 1.4
            self.validate_thread_sharing()
        if self.connection is not None:
            self.connection.disconnect()
            self.connection = None

    def get_connection_params(self):
        ret = {
            'repo_url': self.settings_dict['REPO_URL'],
            'search_url': self.settings_dict.get('SEARCH_URL'),
            'username': self.settings_dict['USERNAME'],
            'password': self.settings_dict['PASSWORD'],
            'options': {
                k if isinstance(k, int) else k.lower(): v
                for k, v in self.settings_dict.get('CONNECTION_OPTIONS', {}).items()
            },
        }
        # if there is no namespace config, create a new default one
        if 'namespace' not in ret['options']:
            ret['options']['namespace'] = NamespaceConfig()
        else:
            ret['options']['namespace'] = NamespaceConfig(**ret['options']['namespace'])

        return ret

    def get_new_connection(self, conn_params):
        connection = FedoraWithElasticConnection(fcrepo_url=conn_params['repo_url'],
                                                 elasticsearch_url=conn_params['search_url'],
                                                 fcrepo_username=conn_params['username'],
                                                 fcrepo_password=conn_params['password'],
                                                 namespace_config=conn_params['options']['namespace'])

        options = conn_params['options']
        for opt, value in options.items():
            if opt == 'page_size':
                self.page_size = int(value)
            else:
                connection.set_option(opt, value)

        return connection

    def init_connection_state(self):
        pass

    def is_usable(self):
        return True

    def create_cursor(self, *args, **kwargs):
        return DatabaseCursor(self.connection)

    def _set_autocommit(self, autocommit):
        pass

    def _start_transaction_under_autocommit(self):
        pass

    def prepare_fedora_options(self, opts):
        return FedoraWithElasticConnection.prepare_fedora_options(opts)


class NamespaceConfig:
    def __init__(self, namespace='', prefix=''):
        self.namespace = namespace
        self.prefix = prefix

    def default_parent_for_inserted_object(self, inserted_object):
        if inserted_object['options']:
            return inserted_object['options'].default_parent
        return None
