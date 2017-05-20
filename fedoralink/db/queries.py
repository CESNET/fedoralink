from rdflib import URIRef

from fedoralink.db.lookups import FedoraMetadataAnnotation
from fedoralink.db.utils import search2rdf
from fedoralink.idmapping import url2id
from fedoralink.models import FedoraResourceUrlField


class FedoraMetadata:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, item):
        if isinstance(item, URIRef):
            item = str(item)
        print(self.data)
        return self.data[item]


class SearchQuery:
    def __init__(self, query, columns, start, end):
        self.query = query
        self.columns = columns
        self.start = start
        self.end = end

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
    def __init__(self, scanner, columns, count):
        self.scanner = scanner
        self.columns = columns
        self.count = count
        self.iter = iter(self.scanner)

    def __next__(self):
        if self.count:
            self.count -= 1
            if not self.count:
                raise StopIteration()

        data = next(self.iter)
        print(self, data['_source'])
        src = data['_source']
        return [
            self.get_column_data(data, src, x) for x in self.columns
        ]

    def get_column_data(self, data, source, column):
        if isinstance(column[3], FedoraMetadataAnnotation):
            return FedoraMetadata({search2rdf(k) : v for k, v in source.items()})
        if column[4] == column[4].model._meta.pk:
            return url2id(data['_id'])
        if isinstance(column[4], FedoraResourceUrlField):
            return data['_id']
        return source[column[1]]


class FedoraResourceScanner:
    def __init__(self, data):
        self.data = data
        self.iter = iter(self.data)

    def __next__(self):
        return next(self.iter)
