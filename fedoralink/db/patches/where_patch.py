#
# in the as_sql, Where uses ' %s ' - if it is moved to ops, we would not need this workaround
#
from django.db.models.sql import EmptyResultSet
from django.db.models.sql.where import AND


def where_as_fedoralink(self, compiler, connection):
    """
    Returns the SQL version of the where clause and the value to be
    substituted in. Returns '', [] if this node matches everything,
    None, [] if this node is empty, and raises EmptyResultSet if this
    node can't match anything.
    """
    result = []
    result_params = []
    if self.connector == AND:
        full_needed, empty_needed = len(self.children), 1
    else:
        full_needed, empty_needed = 1, len(self.children)

    for child in self.children:
        try:
            sql, params = compiler.compile(child)
        except EmptyResultSet:
            empty_needed -= 1
        else:
            if sql:
                result.append(sql)
                result_params.extend(params)
            else:
                full_needed -= 1
        # Check if this node matches nothing or everything.
        # First check the amount of full nodes and empty nodes
        # to make this node empty/full.
        # Now, check if this node is full/empty using the
        # counts.
        if empty_needed == 0:
            if self.negated:
                return '', []
            else:
                raise EmptyResultSet
        if full_needed == 0:
            if self.negated:
                raise EmptyResultSet
            else:
                return '', []
    conn = connection.ops.logical_binary_operation_delimiter_sql() % self.connector
    sql_string = conn.join(result)
    if sql_string:
        if self.negated:
            # Some backends (Oracle at least) need parentheses
            # around the inner SQL in the negated case, even if the
            # inner SQL contains just a single expression.
            sql_string = connection.ops.logical_not_operation_delimiter_sql() % sql_string
        elif len(result) > 1:
            sql_string = connection.ops.logical_group_delimiter_sql() % sql_string
    return sql_string, result_params


# Patch source:
#     """
#     Returns the SQL version of the where clause and the value to be
#     substituted in. Returns '', [] if this node matches everything,
#     None, [] if this node is empty, and raises EmptyResultSet if this
#     node can't match anything.
#     """
#     result = []
#     result_params = []
#     if self.connector == AND:
#         full_needed, empty_needed = len(self.children), 1
#     else:
#         full_needed, empty_needed = 1, len(self.children)
#
#     for child in self.children:
#         try:
#             sql, params = compiler.compile(child)
#         except EmptyResultSet:
#             empty_needed -= 1
#         else:
#             if sql:
#                 result.append(sql)
#                 result_params.extend(params)
#             else:
#                 full_needed -= 1
#         # Check if this node matches nothing or everything.
#         # First check the amount of full nodes and empty nodes
#         # to make this node empty/full.
#         # Now, check if this node is full/empty using the
#         # counts.
#         if empty_needed == 0:
#             if self.negated:
#                 return '', []
#             else:
#                 raise EmptyResultSet
#         if full_needed == 0:
#             if self.negated:
#                 raise EmptyResultSet
#             else:
#                 return '', []
#     conn = ' %s ' % self.connector
#     sql_string = conn.join(result)
#     if sql_string:
#         if self.negated:
#             # Some backends (Oracle at least) need parentheses
#             # around the inner SQL in the negated case, even if the
#             # inner SQL contains just a single expression.
#             sql_string = 'NOT (%s)' % sql_string
#         elif len(result) > 1:
#             sql_string = '(%s)' % sql_string
#     return sql_string, result_params
