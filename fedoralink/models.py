import inspect
from io import BytesIO
import logging
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

import rdflib
from rdflib import Literal, URIRef
from rdflib.namespace import DC, RDF
import inflection as inflection

from fedoralink.fields import DjangoMetadataBridge
from fedoralink.indexer.fields import IndexedField, IndexedLanguageField

from .utils import StringLikeList, OrderableModelList, TypedStream
from .type_manager import FedoraTypeManager
from .fedorans import FEDORA, EBUCORE, FEDORA_INDEX
from .manager import FedoraManager
from .rdfmetadata import RDFMetadata

log = logging.getLogger('fedoralink.models')


def get_from_classes(clazz, class_var):
    """
    Get a list of class variables with the given name in clazz and all its superclasses. The values are returned
    in mro order.

    :param clazz:           the class which is being queried
    :param class_var:       class variable name
    :return:                list of values
    """
    ret = []
    for clz in reversed(inspect.getmro(clazz)):
        if hasattr(clz, class_var):
            val = getattr(clz, class_var)
            if isinstance(val, list) or isinstance(val, tuple):
                ret.extend(val)
            else:
                ret.append(val)
    return ret


class Types:
    """
    Helper class which holds RDF types of the object
    """
    def __init__(self, metadata):
        self.__metadata = metadata

    def add(self, a_type):
        self.__metadata.add(RDF.type, a_type)

    def remove(self, a_type):
        self.__metadata.remove(RDF.type, a_type)

    def __iter__(self):
        return iter(self.__metadata[RDF.type])

    def __str__(self):
        return str(list(iter(self)))


class FedoraObjectMetaclass(type):

    def __init__(cls, name, bases, attrs):
        super(FedoraObjectMetaclass, cls).__init__(name, bases, attrs)
        cls.objects = FedoraManager.get_manager(cls)


class FedoraObject(metaclass=FedoraObjectMetaclass):
    """
    The base class of all Fedora objects, modelled along Django's model

    Most important methods and properties:
        .id
        .children
        .get_bitstream()

        .save()
        .delete()
        .local_bitstream

        .create_child()
        .create_subcollection()

    To get/modify metadata, use [RDF:Name], for example obj[DC.title]. These methods always return a list of metadata.

    """

    post_fetch_hooks = []

    def __init__(self, **kwargs):
        self.metadata     = None
        self.__connection = None
        self.__children   = None
        self.__is_incomplete = False

        if '__metadata' in kwargs:
            self.metadata = kwargs['__metadata']
        else:
            self.metadata   = RDFMetadata('')

        if '__connection' in kwargs:
            self.__connection = kwargs['__connection']
        else:
            self.__connection = None

        if '__slug' in kwargs:
            self.__slug = kwargs['__slug']
        else:
            self.__slug = None

        self.types = Types(self.metadata)

        self.__local_bitstream = None

    # objects are filled in by metaclass, this field is here just to make editors happy
    objects = None

    indexed_fields = []
    """
        Fields that will be used in indexing (LDPath will be created and installed
        when ./manage.py config_index <modelname> is called)
    """

    @classmethod
    def handles_metadata(cls, _metadata):
        """
        Returns priority with which this class is able to handle the given metadata, -1 or None if not at all

        :type _metadata: RDFMetadata
        :param _metadata: the metadata
        :return:         priority
        """

        # although FedoraObject can handle any fedora object, this is hardcoded into FedoraTypeManager,
        # this method returns None so that subclasses that do not override it will not be mistakenly used in
        # type mapping
        return None

    @property
    def slug(self):
        return self.__slug

    def save(self):
        """
        saves this instance
        """
        getattr(type(self), 'objects').save((self,), None)

    @classmethod
    def save_multiple(cls, objects, connection=None):
        """
        saves multiple instances, might optimize the number of calls to Fedora server
        """
        getattr(cls, 'objects').save(objects, connection)

    @property
    def objects_fedora_connection(self):
        """
        returns the connection which created this object
        """
        return self.__connection

    def get_bitstream(self):
        """
        returns a TypedStream associated with this node
        """
        return self.objects.get_bitstream(self)

    def get_local_bitstream(self):
        """
        returns a local bitstream ready for upload
        :returns TypedStream instance
        """
        return self.__local_bitstream

    def set_local_bitstream(self, local_bitstream):
        """
        sets a local bitstream. Call .save() afterwords to send it to the server
        :param local_bitstream instance of TypedStream
        """
        self.__local_bitstream = local_bitstream

    def created(self):
        pass

    @property
    def children(self):
        return self.list_children()

    def list_children(self, refetch=True):
        return OrderableModelList(get_from_classes(type(self), 'objects')[0].load_children(self, refetch), self)

    def create_child(self, child_name, additional_types=None, flavour=None, slug=None):
        child = self._create_child(flavour or FedoraObject, slug)

        if additional_types:
            for t in additional_types:
                child.types.add(t)

        if isinstance(child_name, str):
            child[DC.title] = Literal(child_name)
        elif isinstance(child_name, Literal):
            child[DC.title] = child_name
        else:
            for c in child_name:
                child.metadata.add(DC.title, c)

        child.created()

        return child

    def create_subcollection(self, collection_name, additional_types=None, flavour=None, slug=None):
        types = [EBUCORE.Collection]
        if additional_types:
            types.extend(additional_types)

        return self.create_child(collection_name, types, flavour=flavour, slug=slug)

    def _create_child(self, child_types, slug):

        if not isinstance(child_types, list):
            child_types = [child_types]

        clz = FedoraTypeManager.generate_class(child_types)

        ret = clz(id=None, __connection=self.__connection, __slug=slug)

        ret[FEDORA.hasParent] = rdflib.URIRef(self.id)

        return ret

    def delete(self):
        getattr(type(self), 'objects').delete(self)

    def update(self, fetch_child_metadata=True):
        """
        Fetches new data from server and overrides this object's metadata with them
        """
        self.metadata = getattr(type(self), 'objects').update(self, fetch_child_metadata).metadata

    @property
    def id(self):
        return self.metadata.id

    @property
    def is_incomplete(self):
        return self.__is_incomplete

    @is_incomplete.setter
    def is_incomplete(self, val):
        self.__is_incomplete = val

    def __getitem__(self, item):
        return self.metadata[item]

    def __setitem__(self, key, value):
        self.metadata[key] = value

    def __delitem__(self, key):
        del self.metadata[key]


class UploadedFileStream:

    def __init__(self, file):
        self.file = file
        self.content = BytesIO()
        for c in self.file.chunks():
            self.content.write(c)
        self.content.seek(0)

    def read(self):
        return self.content.read()

    def close(self):
        pass


class IndexableFedoraObjectMetaclass(FedoraObjectMetaclass):

    @staticmethod
    def all_indexed_fields(cls):
        vars = set()
        for clazz in inspect.getmro(cls):
            # un-metaclassed class has fields directly
            for name, fld in inspect.getmembers(clazz, lambda x: isinstance(x, IndexedField)):
                if name not in vars:
                    vars.add(name)
                    fld.name = name
                    yield fld

            # after metaclass, the fields are turned into properties, the original fields are in _meta
            clazz_meta = getattr(clazz, '_meta', None)
            if clazz_meta:
                for fld in clazz_meta.fields:
                    if not fld.name: raise Exception('Name not set, wrong implementation !')
                    if fld.name not in vars:
                        vars.add(fld.name)
                        yield fld

    def __init__(cls, name, bases, attrs):
        super(IndexableFedoraObjectMetaclass, cls).__init__(name, list(bases), attrs)

        def create_property(prop):

            def getter(self):
                if not isinstance(prop, IndexedLanguageField):
                    print("TODO: multiple valued fields ...")
                    # simple type -> return the first item only
                    ret = self.metadata[prop.rdf_name]
                    if len(ret):
                        return ret[0]
                    else:
                        return None

                return StringLikeList(self.metadata[prop.rdf_name])

            def setter(self, value):
                collected_streams = __get_streams(value)
                if len(collected_streams) > 0:
                    if not hasattr(self, '__streams'):
                        setattr(self, '__streams', {})
                    streams = getattr(self, '__streams')
                    streams[prop] = collected_streams
                else:
                    self.metadata[prop.rdf_name] = value

            def __get_streams(value):
                streams = []
                if isinstance(value, tuple) or isinstance(value, list):
                    for x in value:
                        rr = __get_streams(x)
                        streams.extend(rr)
                elif isinstance(value, UploadedFile) or isinstance(value, TypedStream):
                    streams.append(value)
                return streams

            return property(getter, setter)

        indexed_fields = tuple(IndexableFedoraObjectMetaclass.all_indexed_fields(cls))
        for p in indexed_fields:
            setattr(cls, p.name, create_property(p))

        # store django _meta
        cls._meta = DjangoMetadataBridge(cls, indexed_fields)

class IndexableFedoraObject(FedoraObject, metaclass=IndexableFedoraObjectMetaclass):
    def created(self):
        super().created()
        self.types.add(FEDORA_INDEX.Indexable)

        self[FEDORA_INDEX.hasIndexingTransformation] = Literal(self.get_indexer_transform())

    def get_indexer_transform(self):
        return inflection.underscore(type(self).__name__.replace('_bound', ''))

    def full_clean(self, exclude=[], validate_unique=False):
        errors = {}
        for fld in self.indexed_fields:
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
