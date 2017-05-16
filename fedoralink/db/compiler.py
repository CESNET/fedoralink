from __future__ import unicode_literals

from django.db.models.sql import compiler

from fedoralink.db.connection import FedoraWithElasticConnection
from .elasticsearch_connection import ElasticsearchMixin

integer_types = (int,)


class SQLCompiler(compiler.SQLCompiler):

    def compile(self, node, *args, **kwargs):
        return super().compile(node, *args, **kwargs)

    def execute_sql(self, result_type=compiler.SINGLE):
        return super().execute_sql(result_type)

    def as_sql(self, with_limits=True, with_col_aliases=False, subquery=False):
        return ElasticsearchMixin.get_query_representation(self.query, self)

    def has_results(self):
        import inspect
        iterator = self.results_iter()
        if inspect.isgenerator(iterator):
            try:
                iterator.next()
                return True
            except:
                return False
        else:
            return False


class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):

    def as_sql(self, with_limits=True, with_col_aliases=False, subquery=False):
        return FedoraWithElasticConnection.get_insert_representation(self.query, self)

    def prepare_value(self, field, value):
        return super().prepare_value(field, value)


class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    def execute_sql(self):
        raise NotImplementedError()


class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    def execute_sql(self):
        raise NotImplementedError()


class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    def execute_sql(self):
        raise NotImplementedError()
