import logging

from .elasticsearch_connection import ElasticsearchMixin, InsertScanner, SearchQuery, InsertQuery
from .fedora_connection import FedoraMixin

log = logging.getLogger(__file__)


class FedoraWithElasticConnection(ElasticsearchMixin, FedoraMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_option(self, option_name, option_value):
        setattr(self, option_name, option_value)

    def disconnect(self):
        pass

    def execute_insert(self, query):
        ids = FedoraMixin.create_resources(self, query)
        ElasticsearchMixin.index_resources(self, query, ids)
        return InsertScanner([[self.string2int(object_id)] for object_id in ids])

    def execute(self, query, params):
        if isinstance(query, SearchQuery):
            return self.execute_search(query)
        elif isinstance(query, InsertQuery):
            return self.execute_insert(query)
        else:
            raise NotImplementedError('This type of query is not yet implemented')


    @staticmethod
    def get_insert_representation(query, compiler):
        opts = query.get_meta()

        ElasticsearchMixin._prepare_fedora_options(opts)

        has_fields = bool(query.fields)
        fields = query.fields if has_fields else [opts.pk]

        if has_fields:
            value_rows = [
                {
                    'parent': getattr(obj, '_fedora_parent', None),
                    'doc_type': opts.label,
                    'fields': {
                        (field.fedora_options.rdf_name, field.fedora_options.search_name):
                            compiler.prepare_value(field, compiler.pre_save_val(field, obj))
                        for field in fields
                    }
                }
                for obj in query.objs
            ]
        else:
            value_rows = [{} for _ in query.objs]

        yield InsertQuery(value_rows), {}

    @staticmethod
    def string2int(x):
        ret = 0
        for d in x.encode('utf-8'):
            ret = ret * 256 + int(d)
        return ret

    @staticmethod
    def int2string(x):
        ret = []
        while x:
            ret.append(chr(x % 256))
            x = x // 256
        ret.reverse()
        return bytes(ret).decode('utf-8')

