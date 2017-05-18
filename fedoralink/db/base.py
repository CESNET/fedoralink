from __future__ import unicode_literals

import logging

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.base.validation import BaseDatabaseValidation

from fedoralink.db import FedoraError
from fedoralink.db.connection import FedoraWithElasticConnection
from fedoralink.db.cursor import DatabaseCursor

log = logging.getLogger(__file__)


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


class DatabaseOperations(BaseDatabaseOperations):
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

class DatabaseValidation(BaseDatabaseValidation):
    pass


class FedoraDatabase(object):
    # Base class for all exceptions
    Error = FedoraError

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

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.creation = DatabaseCreation(self)
        self.features = DatabaseFeatures(self)
        self.introspection = DatabaseIntrospection(self)
        self.ops = DatabaseOperations(self)
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

    def create_cursor(self):
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
        return inserted_object['doc_type']
