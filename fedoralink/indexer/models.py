import inspect

import inflection as inflection
from django.core.exceptions import ValidationError
from django.db.models.signals import class_prepared
from rdflib import Literal, XSD

from fedoralink.fedorans import FEDORA_INDEX
from fedoralink.indexer.fields import IndexedField
from fedoralink.models import FedoraObjectMetaclass, DjangoMetadataBridge, OldFedoraObject
from fedoralink.type_manager import FedoraTypeManager


class IndexableFedoraObjectMetaclass(FedoraObjectMetaclass):

    @staticmethod
    def all_indexed_fields(cls):
        vars = set()
        for clazz in reversed(inspect.getmro(cls)):
            # un-metaclassed class has fields directly
            flds = list(inspect.getmembers(clazz, lambda x: isinstance(x, IndexedField)))
            flds.sort(key=lambda x: x[1].order)
            for name, fld in flds:
                if name not in vars:
                    vars.add(name)
                    fld.name = name
                    fld.editable = True
                    yield fld

            # after metaclass, the fields are turned into properties, the original fields are in _meta
            clazz_meta = getattr(clazz, '_meta', None)
            if clazz_meta:
                for fld in clazz_meta.fields:
                    if not fld.name: raise Exception('Name not set, wrong implementation !')
                    if fld.name not in vars:
                        vars.add(fld.name)
                        fld.editable = True
                        yield fld

    @staticmethod
    def fill_from_meta(cls):

        props = {}
        for clazz in inspect.getmro(cls):
            clazz_meta = getattr(clazz, '_meta', None)
            if clazz_meta:
                IndexableFedoraObjectMetaclass._merge_meta(clazz_meta, props)
            clazz_meta = getattr(clazz, 'Meta', None)
            if clazz_meta:
                IndexableFedoraObjectMetaclass._merge_meta(clazz_meta, props)

        return props

    @staticmethod
    def _merge_meta(clazz_meta, props):
        for prop in dir(clazz_meta):
            if prop.startswith('_'):
                continue
            val = getattr(clazz_meta, prop)
            vals = props.setdefault(prop, [])
            if isinstance(val, list) or isinstance(val, tuple):
                for v in val:
                    if v not in vals:
                        vals.append(v)
            else:
                if not val in vals:
                    vals.append(val)

    def __init__(cls, name, bases, attrs):
        super(IndexableFedoraObjectMetaclass, cls).__init__(name, list(bases), attrs)

        indexed_fields = tuple(IndexableFedoraObjectMetaclass.all_indexed_fields(cls))
        processed_rdf_names = set()
        for p in indexed_fields:
            if p.rdf_name in processed_rdf_names:
                raise AttributeError("Property with rdf name %s already implemented" % p.rdf_name)
            processed_rdf_names.add(p.rdf_name)
            p.instrument(cls, p.name)

        # store django _meta
        cls._meta = DjangoMetadataBridge(cls, indexed_fields)

        for k, v in IndexableFedoraObjectMetaclass.fill_from_meta(cls).items():
            if not hasattr(cls._meta, k):
                # print("Setting on %s: %s -> %s" % (cls, k, v))
                setattr(cls._meta, k, v)
            else:
                # print("Ignoring on %s: %s" % (cls, k))
                pass

        if not hasattr(cls._meta, 'rdf_types'):
            setattr(cls._meta, 'rdf_types', ())

        application = cls.__module__ + "." + cls.__class__.__name__
        application = application.split('.')[:-1]
        if application and application[-1] == 'models':
            application = application[:-1]

        setattr(cls._meta, 'application', '.'.join(application))

        if cls._meta.rdf_types and not cls.__name__.endswith('_bound'):
            FedoraTypeManager.register_model(cls, on_rdf_type=cls._meta.rdf_types)

        class_prepared.send(sender=cls)


class IndexableFedoraObject(OldFedoraObject, metaclass=IndexableFedoraObjectMetaclass):
    def created(self):
        super().created()
        self.types.add(FEDORA_INDEX.Indexable)
        for rdf_type in self._meta.rdf_types:
            self.types.add(rdf_type)

        self[FEDORA_INDEX.hasIndexingTransformation] = Literal(self.get_indexer_transform(), datatype=XSD.string)

    def get_indexer_transform(self):
        return inflection.underscore(type(self).__name__.replace('_bound', ''))

    def full_clean(self, exclude=[], validate_unique=False):
        errors = {}
        for fld in self._meta.fields:
            if fld.required:
                if not getattr(self, fld.name):
                    errors[fld.name] = "Field %s is required" % fld.name

        if errors:
            raise ValidationError(errors)

    def validate_unique(self, exclude=[]):
        pass

    @property
    def pk(self):
        return self.id


def fedoralink_classes(obj):
    """
    Get the original fedoralink classes of of a given object. They might be different to real classes (via getmro) because
    fedoralink autogenerates types when deserializing from RDF metadata/Indexer data.

    :param obj: an instance of FedoraObject
    :return:    list of classes
    """
    # noinspection PyProtectedMember
    return obj._type


def fedoralink_streams(obj):
    """
    Return an iterator of tuples (field, instance of TypedStream or UploadedFile)
    that were registered (via setting an instance of these classes
    to any property) with the object.

    :param obj: an instance of FedoraObject
    :return:    iterator of tuples
    """
    return getattr(obj, '__streams', {}).items()


def fedoralink_clear_streams(obj):
    """
    Removes registered streams from an instance of FedoraObject

    :param obj: instance of FedoraObject
    """
    setattr(obj, '__streams', {})