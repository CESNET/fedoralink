from __future__ import unicode_literals

from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.validation import BaseDatabaseValidation
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from fedoralink.db import FedoraError
from fedoralink.db.connection import FedoraWithElasticConnection


class DatabaseCreation(BaseDatabaseCreation):
    def _clone_test_db(self, number, verbosity, keepdb=False):
        raise Exception("Not implemented")

    def create_test_db(self, *args, **kwargs):
        raise Exception("Not implemented")

    def destroy_test_db(self, *args, **kwargs):
        raise Exception("Not implemented")


class DatabaseCursor(object):
    def __init__(self, connection):
        self.connection          = connection
        self.current_query       = None
        self.current_params      = None
        self.scanner             = None
        self.lastrowid           = None

    def close(self):
        self.connection.disconnect()

    def execute(self, query, params):
        self.current_query = query
        self.current_params = params
        self.scanner = self.connection.execute(query, params)

    def executemany(self, sql, params):
        """ Repeatedly executes a SQL statement. """
        raise NotImplementedError('Not yet implemented')

    def fetchall(self):
        """ Fetches all rows from the resultset. """
        raise NotImplementedError('Not yet implemented')

    def fetchmany(self, n):
        """ Fetches several rows from the resultset. """
        ret = []
        for i in range(n):
            try:
                ret.append(next(self.scanner))
            except StopIteration:
                break
        return ret

    def fetchone(self):
        """ Fetches one row from the resultset. """
        raise NotImplementedError('Not yet implemented')

    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError('Not yet implemented')



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


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "fedoralink.db.compiler"

    def quote_name(self, name):
        return name

    def no_limit_value(self):
        return -1

    # do not transform datetime to string, just return the datetime - both fedora and elastic can handle it
    def adapt_datetimefield_value(self, value):
        return value


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
        self.connection.connection.update_elasticsearch_index(model)


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
        connection = FedoraWithElasticConnection(fcrepo_url        = conn_params['repo_url'],
                                                 elasticsearch_url = conn_params['search_url'],
                                                 fcrepo_username   = conn_params['username'],
                                                 fcrepo_password   = conn_params['password'],
                                                 namespace_config  = conn_params['options']['namespace'])

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


class NamespaceConfig:
    def __init__(self, namespace='', prefix=''):
        self.namespace = namespace
        self.prefix = prefix

    def default_parent_for_inserted_object(self, inserted_object):
        return inserted_object['doc_type']