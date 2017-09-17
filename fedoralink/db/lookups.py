from django.db.models import Field, CharField, Count, ForeignKey
from django.db.models.expressions import Col, Value
from django.db.models.sql.where import WhereNode

from fedoralink.db.patches.where_patch import where_as_fedoralink


class FedoraMetadataAnnotation(Value):
    def __init__(self):
        super().__init__('Something weird happened, this value should have been replaced with fedora metadata',
                         CharField())


def unimplemented_lookup(self, compiler, connection):
    raise NotImplementedError('Lookup of type %s is not implemented in fedoralink' % type(self))


class Node:
    pass


class Column(Node):
    def __init__(self, rdf_name, search_name, django_field):
        self.rdf_name = rdf_name
        self.search_name = search_name
        self.django_field = django_field


class Operation(Node, str):
    def __new__(cls, operation_type, *operands):
        return str.__new__(cls, '%s[%s]' % (operation_type, operands))

    def __init__(self, operation_type, *operands):
        super().__init__()
        if isinstance(operation_type, Operation):
            # copy constructor
            self.operation_type = operation_type.operation_type
            self.operands = operation_type.operands
        else:
            self.operation_type = operation_type
            self.operands = list(operands)

    def join(self, arr):
        self.operands.extend(arr)
        return self

    def __str__(self):
        # sometimes django casts an instance of operation to string - this is to prevent the casting
        # so that we do not have to override a lot of django code and remove the str(...)
        return self


class FedoraIdColumn(Column):
    def __init__(self, field):
        super().__init__('_id', '_id', field)


def col_lookup(self, compiler, connection):
    field = self.field
    model = self.field.model
    opts = model._meta
    connection.prepare_fedora_options(opts)
    if field.column == 'fedora_id':
        return FedoraIdColumn(field), []
    fedora_field_options = field.fedora_options
    return Column(fedora_field_options.rdf_name, fedora_field_options.search_name, field), []


def _generic_lookup(self, compiler, connection):
    lhs, lhs_params = self.process_lhs(compiler, connection)
    rhs, rhs_params = self.process_rhs(compiler, connection)
    if lhs_params or rhs_params:
        raise NotImplementedError('Params in lookups are not supported')
    return Operation(self.lookup_name, lhs, rhs), []


exact_lookup        = _generic_lookup


# TODO: for now, there is no easy way of icontains in ES, so making it the same as contains
contains_lookup     = _generic_lookup
icontains_lookup    = _generic_lookup

# TODO: for now, there is no easy way of istartswith in ES, so making it the same as startswith
startswith_lookup   = _generic_lookup
istartswith_lookup  = _generic_lookup


def in_lookup(self, compiler, connection):
    lhs, lhs_params = self.process_lhs(compiler, connection)
#    rhs, rhs_params = self.process_rhs(compiler, connection)
    db_rhs = getattr(self.rhs, '_db', None)
    if db_rhs is not None and db_rhs != connection.alias:
        raise ValueError(
            "Subqueries aren't allowed across different databases. Force "
            "the inner query to be evaluated using `list(inner_query)`."
        )

    if self.rhs_is_direct_value():
        try:
            rhs = set(self.rhs)
        except TypeError:  # Unhashable items in self.rhs
            rhs = self.rhs
        rhs_params = None

        if not rhs:
            from django.db.models.sql.datastructures import EmptyResultSet
            raise EmptyResultSet
    else:
        raise ValueError("Non-direct RHS not yet supported")

    if lhs_params or rhs_params:
        raise NotImplementedError('Params in lookups are not supported')
    return Operation(self.lookup_name, lhs, rhs), []


def get_db_prep_lookup(self, value, connection, orig_lookup):
    # if is fedoralink, return just the value, otherwise return original prep lookup value
    if connection.vendor == 'fedoralink':
        return value, []  # no need to return '%s' or similar as query is a json ...
    return orig_lookup(self, value, connection)


def patch_get_db_prep_lookup(lookup):
    prev = lookup.get_db_prep_lookup
    lookup.get_db_prep_lookup = lambda self, value, connection: get_db_prep_lookup(self, value, connection, prev)


def add_vendor_to_lookups():
    for lookup in Field.class_lookups.values():
        if lookup.lookup_name + '_lookup' in globals():
            lookup.as_fedoralink = globals()[lookup.lookup_name + '_lookup']
        else:
            lookup.as_fedoralink = unimplemented_lookup
        patch_get_db_prep_lookup(lookup)

    Col.as_fedoralink = col_lookup
    WhereNode.as_fedoralink = where_as_fedoralink


# TODO: remove col_rdf_name
def get_column_ids(columns, add_count=None):
    ret = []
    for col in columns:
        if add_count and not isinstance(col[0], Count):
            continue
        fedora_col = col[1][0]

        if isinstance(col[0], FedoraMetadataAnnotation):
            django_field = col[0].field
            ret.append(
                (
                    None,
                    None,
                    None,
                    col[0],
                    django_field
                )
            )
            continue

        if hasattr(col[0], 'target'):
            django_field = col[0].target
        else:
            django_field = col[0].field

        if isinstance(col[0], Count):
            pass
        elif not isinstance(fedora_col, Column):
            raise NotImplementedError('Returning column of type %s is not yet implemented' % type(fedora_col))

        opts = getattr(django_field, 'fedora_options', None)
        col_rdf_name = None
        if opts:
            rdf_name = opts.rdf_name
            search_name = opts.search_name
            if isinstance(django_field, ForeignKey):
                col_rdf_name = rdf_name
            else:
                col_rdf_name = fedora_col.rdf_name
        else:
            if isinstance(fedora_col, FedoraIdColumn):
                rdf_name = '_id'
                search_name = '_id'
                col_rdf_name = fedora_col.rdf_name
            elif isinstance(col[0], Count):
                rdf_name = '__count'
                search_name = '__count'
            else:
                raise AttributeError('Do not have mapping for column %s' % col)

        ret.append(
            (
                rdf_name,
                search_name,
                col_rdf_name,
                fedora_col,
                django_field
            ))
    return ret
