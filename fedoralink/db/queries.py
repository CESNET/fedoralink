import dateutil.parser
from rdflib import URIRef, Literal

from fedoralink.db.lookups import FedoraMetadataAnnotation
from fedoralink.db.rdf import RDFMetadata
from fedoralink.db.utils import search2rdf
from fedoralink.fields import FedoraField
from fedoralink.idmapping import url2id
from fedoralink.models import FedoraResourceUrlField


class FedoraMetadata:
    def __init__(self, data, from_search, doc_type=None):
        if isinstance(data, RDFMetadata):
            self.data = data
        else:
            self.data = {
                k:self._convert(v) for k, v in data.items()
            }
        self.data = data
        self.from_search = from_search
        self.doc_type = doc_type

    def __getitem__(self, item):
        if not isinstance(item, URIRef):
            item = URIRef(item)
        print(self.data)
        return self.data[item]

    def _convert(self, val):
        if isinstance(val, list):
            ret = []
            for x in val:
                ret.extend(self._convert(x))
            return ret
        if isinstance(val, URIRef) or isinstance(val, Literal):
            return [val]
        return [Literal(val)]

    def get(self, key, defaultval=None):
        if not isinstance(key, URIRef):
            key = URIRef(key)
        try:
            return self.data[key]
        except:
            return defaultval


class SearchQuery:
    def __init__(self, query, columns, start, end, use_search_instead_of_scan):
        self.query = query
        self.columns = columns
        self.start = start
        self.end = end
        self.use_search_instead_of_scan = use_search_instead_of_scan

    @property
    def count(self):
        if self.start is None or self.end is None:
            return None
        return self.end - self.start


class FedoraQueryByPk:
    def __init__(self, query, pk, compiler):
        self.query = query
        self.pk = pk
        self.compiler = compiler


class FedoraUpdateQuery:
    def __init__(self, pk, update_data, prev_data, patched_instance):
        self.pk = pk
        self.update_data = update_data
        self.prev_data = prev_data
        self.patched_instance = patched_instance


class InsertQuery:
    def __init__(self, objects):
        self.objects = objects


class InsertScanner:
    def __init__(self, data):
        self.data = data
        self.iter = iter(data)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iter)


class SelectScanner:
    def __init__(self, scanner, columns, count, mapping_cache, result_metadata=None):
        self.scanner = scanner
        self.columns = columns
        self.count = count
        self.iter = iter(self.scanner)
        self.mapping_cache = mapping_cache
        self.result_metadata = result_metadata
        self.eof = False

    def __next__(self):
        if self.eof:
            raise StopIteration()

        if self.count:
            self.count -= 1
            if not self.count:
                self.eof = True

        data = next(self.iter)
        print(self, data['_source'])
        src = data['_source']
        mapping = self.mapping_cache[data['_type']]
        return [
            self.get_column_data(data, src, x, mapping) for x in self.columns
        ]

    def get_column_data(self, data, source, column, mapping):
        if isinstance(column[3], FedoraMetadataAnnotation):
            return FedoraMetadata({
                search2rdf(k) : self._apply_mapping(mapping, k, v) for k, v in source.items()
            }, from_search=True, doc_type=data['_type'])
        if column[0] == '__count':
            return self.result_metadata['total']
        if column[4] == column[4].model._meta.pk:
            return url2id(data['_id'])
        if isinstance(column[4], FedoraResourceUrlField):
            return URIRef(data['_id'])
        if isinstance(column[4], FedoraField):
            items = source[column[1]]
            if not isinstance(items, list):
                items = [items]
            return [Literal(x) for x in items]
        return source[column[1]]

    def _apply_mapping(self, mapping, key, val):
        mapping = mapping.get(key, None)
        if not mapping:
            return val
        _type = mapping['type']
        if _type == 'keyword':
            return val
        if _type == 'date':
            return dateutil.parser.parse(val)
        raise NotImplementedError('Deserialization of type %s not yet implemented' % _type)


class FedoraResourceScanner:
    def __init__(self, data):
        self.data = data
        self.iter = iter(self.data)

    def __next__(self):
        return next(self.iter)
