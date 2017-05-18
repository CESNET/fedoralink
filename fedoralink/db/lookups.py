from django.db.models import Field
from django.db.models.expressions import Col


def unimplemented_lookup(self, compiler, connection):
    raise NotImplementedError('Lookup of type %s is not implemented in fedoralink' % type(self))


class Node:
    pass


class Column(Node):
    def __init__(self, name):
        self.name = name


class FedoraIdColumn(Column):
    def __init__(self):
        super().__init__('_id')


def col_lookup(self, compiler, connection):
    field = self.field
    model = self.field.model
    opts = model._meta
    connection.prepare_fedora_options(opts)
    if not hasattr(field, 'fedora_options'):
        if field.column == 'fedora_id':
            return FedoraIdColumn(), []
    fedora_field_options = field.fedora_options
    return Column(fedora_field_options.rdf_name), []


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
        lookup.as_fedoralink = unimplemented_lookup
        patch_get_db_prep_lookup(lookup)

    Col.as_fedoralink = col_lookup


def get_column_ids(columns):
    ret = []
    for col in columns:
        fedora_col = col[1][0]
        if not isinstance(fedora_col, Column):
            raise NotImplementedError('Returning column of type %s is not yet implemented' % type(fedora_col))
        django_field = col[0].field
        opts = getattr(django_field, 'fedora_options', None)
        if opts:
            rdf_name = opts.rdf_name
            search_name = opts.search_name
        else:
            if isinstance(fedora_col, FedoraIdColumn):
                rdf_name = '_id'
                search_name = '_id'
            else:
                raise AttributeError('Do not have mapping for column %s' % col)

        ret.append(
            (
                rdf_name,
                search_name,
                fedora_col.name,
                fedora_col,
                django_field
            ))
    return ret
