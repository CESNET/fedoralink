import traceback
import urllib
import urllib.parse

import base64
import fedoralink
from dateutil.parser import parse
from elasticsearch import Elasticsearch
from rdflib import Literal, URIRef, RDF

from fedoralink.fedorans import FEDORA
from fedoralink.indexer import Indexer, IndexedField, FEDORA_TYPE_FIELD, FEDORA_PARENT_FIELD
from fedoralink.models import IndexableFedoraObject


class ElasticIndexer(Indexer):

    def __init__(self, repo_conf):
        url = urllib.parse.urlsplit(repo_conf['SEARCH_URL'])
        self.index_name = url.path

        while self.index_name.startswith('/'):
            self.index_name = self.index_name[1:]
        while self.index_name.endswith('/'):
            self.index_name = self.index_name[:-1]

        self.es = Elasticsearch(({"host": url.hostname, "port": url.port}, ))

        if not self.es.indices.exists(self.index_name):
            self.es.indices.create(index=self.index_name)

    # abstract method
    def search(self, query, model_class, start, end, facets, ordering, values):
        raise Exception("Please reimplement this method in inherited classes")

    def save_mapping(self, class_name, mapping):
        return self.es.indices.put_mapping(index=self.index_name, doc_type=class_name, body=mapping)

    def get_mapping(self, class_name):
        return self.es.indices.get_mapping(index=self.index_name, doc_type=class_name)

    def reindex(self, obj):

        def convert(data, field):
            if isinstance(data, Literal):
                data = data.value

            if isinstance(data, URIRef):
                indexer_data[field.name] = str(data)

            if 'lang' in field.field_type:
                lng = {}
                for d in data:
                    lang = d.language
                    if not lang:
                        lang = 'null'
                    lng[lang] = str(d)
                return lng

            if isinstance(data, list):
                return [convert(x, field) for x in data]

            elif 'date' in field.field_type:
                if isinstance(data, str):
                    data = parse(data)
                return data.strftime('%Y-%m-%dT%H:%M:%S')


            return data

        clz = obj._type[0]
        doc_type = clz.__module__.replace('.', '_') + "_" + clz.__name__

        if not issubclass(clz, IndexableFedoraObject):
            # can not reindex something which does not have a mapping
            return

        indexer_data = {}
        for field in clz.indexed_fields:
            data = getattr(obj, field.name)
            if data is None:
                continue

            indexer_data[field.name] = convert(data, field)

        id = base64.b64encode(str(obj.pk).encode('utf-8')).decode('utf-8')

        indexer_data['__fedora__id'] = obj.pk
        indexer_data['__fedora__parent'] = convert(obj[FEDORA.hasParent], FEDORA_PARENT_FIELD)
        indexer_data['__fedora__type'] = convert(obj[RDF.type], FEDORA_TYPE_FIELD)

        # print(indexer_data)
        try:
            self.es.index(index=self.index_name, doc_type=doc_type, body=indexer_data, id=id)
        except:
            print("Exception in indexing, data", indexer_data)
            traceback.print_exc()
