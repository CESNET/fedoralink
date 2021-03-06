import json
import logging

from django.conf import settings
from django.core.management import BaseCommand
from django.db import connections

from fedoralink.indexer.elastic import FEDORA_ID_FIELD, FEDORA_PARENT_FIELD, FEDORA_TYPE_FIELD, FEDORALINK_TYPE_FIELD, \
    FEDORA_CREATED_FIELD, FEDORA_LAST_MODIFIED_FIELD, CESNET_RDF_TYPES
from fedoralink.indexer.fields import IndexedLanguageField, IndexedIntegerField, IndexedDateTimeField, IndexedTextField, \
    IndexedLinkedField, IndexedBinaryField, IndexedDateField, IndexedGPSField
from fedoralink.type_manager import FedoraTypeManager
from fedoralink.utils import url2id, id2url

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('config_repository_index')

import importlib

def class_for_name(module_name, class_name):

    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c

class Command(BaseCommand):
    args = '<model name>*'
    help = """

        Configures elasticsearch index

        Arguments for this command is a list of classes. All the classes are read, their
        'indexed_fields' are inspected and an index is created for each of the classes.

    """
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument('model_name', nargs='+')

    def handle(self, *args, **options):

        FedoraTypeManager.populate()

        models = options['model_name']

        for model_name in models:
            fields = {}

            split_model_name  = model_name.split('.')
            indexer_model_name = '_'.join(split_model_name)
            module_name = '.'.join(split_model_name[:-1])
            split_model_name  = split_model_name[-1]
            class_for_name(module_name, split_model_name)
            modelclz = FedoraTypeManager.get_model_class(split_model_name)

            for field in modelclz._meta.fields:
                fldname = url2id(field.rdf_name)
                if fldname not in fields:
                    fields[fldname] = field

            indexer = connections['repository'].indexer

            existing_mapping = indexer.get_mapping(indexer_model_name)
            existing_properties = existing_mapping.get('properties', {})

            new_mapping = {
            }

            new_properties = {
            }

            fields['_fedora_id']            = FEDORA_ID_FIELD
            fields['_fedora_parent']        = FEDORA_PARENT_FIELD
            fields['_fedora_type']          = FEDORA_TYPE_FIELD
            fields['_fedoralink_model']     = FEDORALINK_TYPE_FIELD
            fields['_fedora_created']       = FEDORA_CREATED_FIELD
            fields['_fedora_last_modified'] = FEDORA_LAST_MODIFIED_FIELD
            fields['_collection_child_types'] = CESNET_RDF_TYPES

            print('ADD fields to mapping')

            for fldname, field in fields.items():
                if fldname in existing_properties:
                    continue

                props = {}
                new_properties[fldname] = props

                if isinstance(field, IndexedLanguageField):
                    props['type'] = 'nested'
                    props["include_in_root"] = 'true'
                    props['properties'] = self.gen_languages_mapping(fldname + ".")
                elif isinstance(field, IndexedTextField):
                    props['type']  = 'keyword'
                    props['copy_to'] = fldname + "__fulltext"
                    new_properties[fldname + "__fulltext"] = {
                        'type': 'text',
                    }
                elif isinstance(field, IndexedDateTimeField):
                    props['type'] = 'date'
                elif isinstance(field, IndexedDateField):
                    props['type'] = 'date'
                elif isinstance(field, IndexedIntegerField):
                    props['type'] = 'long'
                elif isinstance(field, IndexedGPSField):
                    props['type'] = 'keyword'
                elif isinstance(field, IndexedLinkedField) or isinstance(field, IndexedBinaryField) :
                    props['type'] = 'keyword'
                else:
                    raise Exception("Mapping type %s not handled yet" % type(field))

            new_mapping['_all'] = {
                "store": True
            }

            new_mapping['properties'] = new_properties
            print(json.dumps(new_mapping, indent=4))

            indexer.save_mapping(indexer_model_name, new_mapping)


    @staticmethod
    def gen_languages_mapping(prefix):
        ret = {
            lang[0] : {
                'type': 'keyword',
                'copy_to': [prefix + 'all', prefix + 'all__fulltext', prefix + lang[0] + "__fulltext"],
            } for lang in settings.LANGUAGES
        }

        ret.update({
            lang[0] + "__fulltext" : {
                'type': 'text',
                'analyzer': 'czech' if lang[0] == 'cs' else 'english',
                'store': True
            } for lang in settings.LANGUAGES
        })

        ret['null'] = {
            'type' : 'keyword',
            'copy_to': [prefix + 'all', prefix + 'all__fulltext', prefix + 'null__fulltext']
        }
        ret['all']  = {
            'type' : 'keyword'
        }

        ret['null__fulltext'] = {'type' : 'text', 'store': True}
        ret['all__fulltext']  = {'type' : 'text', 'store': True}

        return ret
