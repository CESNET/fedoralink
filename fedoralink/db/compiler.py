from __future__ import unicode_literals

from django.db.models import Value, CharField
from django.db.models.sql import compiler
from django.db.models.sql.constants import SINGLE

from fedoralink.db.connection import FedoraWithElasticConnection
from fedoralink.db.lookups import FedoraMetadataAnnotation

integer_types = (int,)


class SQLCompiler(compiler.SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False, subquery=False):
        with self.connection.cursor() as cursor:
            return cursor.connection.get_query_representation(self.query, self, self.connection)

    def has_results(self):
        ret = self.execute_sql(SINGLE)
        return ret is not None


class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False, subquery=False):
        return FedoraWithElasticConnection.get_insert_representation(self.query, self)

    def prepare_value(self, field, value):
        return super().prepare_value(field, value)


class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    def execute_sql(self, *args, **kwargs):
        raise NotImplementedError()


class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    def as_sql(self):
        with self.connection.cursor() as cursor:
            return cursor.connection.get_update_representation(self.query, self, self.connection)



class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False, subquery=False):
        with self.connection.cursor() as cursor:
            return cursor.connection.get_query_representation(self.query, self, self.connection)

    # def execute_sql(self, *args, **kwargs):
    #     raise NotImplementedError()
