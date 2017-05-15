import datetime
import traceback

import django.db.models
import django.forms
from dateutil import parser
from django.apps import apps
from django.core.files.uploadedfile import UploadedFile
from django.db.models.signals import class_prepared
from rdflib import Literal, XSD, URIRef

from fedoralink.fedorans import FEDORA
from fedoralink.forms import LangFormTextField, LangFormTextAreaField, MultiValuedFedoraField, GPSField, \
    FedoraChoiceField, LinkedField
from fedoralink.utils import StringLikeList, TypedStream


class IndexedField:
    __global_order = 0

    MANDATORY   = 'mandatory'
    RECOMMENDED = 'recommended'
    OPTIONAL    = "optional"

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False, attrs=None, level=None):
        self.rdf_name     = rdf_name
        self.required     = required
        self.verbose_name = verbose_name
        self.attrs        = attrs if attrs else {}
        self.multi_valued = multi_valued
        self.order = IndexedField.__global_order
        if level is None:
            if required:
                level = IndexedField.MANDATORY
            else:
                level = IndexedField.OPTIONAL
        self.level = level
        IndexedField.__global_order += 1

    def convert_to_rdf(self, value):
        raise Exception("Conversion to RDF on %s not supported yet" % type(self))

    def convert_from_rdf(self, value):
        raise Exception("Conversion from RDF on %s not supported yet" % type(self))

    def _getter(self, object_instance):

        ret = object_instance.metadata[self.rdf_name]

        if not self.multi_valued:
            # simple type -> return the first item only
            if len(ret):
                return self.convert_from_rdf(ret[0])
            else:
                return None

        return StringLikeList([self.convert_from_rdf(x) for x in object_instance.metadata[self.rdf_name]])

    def _setter(self, object_instance, value):
        collected_streams = self.__get_streams(value)
        if len(collected_streams) > 0:
            if not hasattr(object_instance, '__streams'):
                setattr(object_instance, '__streams', {})
            streams = getattr(object_instance, '__streams')
            streams[self] = collected_streams
        else:
            if isinstance(value, list) or isinstance(value, tuple):
                value = [self.__convert_to_rdf(x) for x in value]
            else:
                value = self.__convert_to_rdf(value)

            object_instance.metadata[self.rdf_name] = value

    def __convert_to_rdf(self, data):
        if data is None:
            return []

        return self.convert_to_rdf(data)

    def __get_streams(self, value):
        streams = []
        if isinstance(value, tuple) or isinstance(value, list):
            for x in value:
                rr = self.__get_streams(x)
                streams.extend(rr)
        elif isinstance(value, UploadedFile) or isinstance(value, TypedStream):
            streams.append(value)
        return streams

    def instrument(self, model_class, name):
        fld = self

        def getter(inst):
            return fld._getter(inst)

        def setter(inst, value):
            fld._setter(inst, value)

        setattr(model_class, name, property(getter, setter))


class IndexedLanguageField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, required=False, verbose_name=None,
                 multi_valued=False, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def formfield(self, **kwargs):
        if 'textarea' in self.attrs.get('presentation', ''):
            defaults = {'form_class': LangFormTextAreaField}
        else:
            defaults = {'form_class': LangFormTextField}

        defaults.update(kwargs)
        return super().formfield(**defaults)

    @staticmethod
    def _convert_val_to_rdf(x):
        if isinstance(x, Literal):
            if x.datatype:
                return x
            if x.language:
                return Literal(x.value, lang=x.language)
            return Literal(x.value, datatype=XSD.string)
        return Literal(x if isinstance(x, str) else str(x), datatype=XSD.string)

    def convert_to_rdf(self, value):
        return IndexedLanguageField._convert_val_to_rdf(value)

    def convert_from_rdf(self, value):
        return StringLikeList(value)

    def _getter(self, object_instance):
        ret = object_instance.metadata[self.rdf_name]
        return self.convert_from_rdf(ret)


class IndexedTextField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False,
                 attrs=None, help_text=None, level=None, choices=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text, choices=choices)

    def formfield(self, **kwargs):
        if self.choices:
            defaults = {'choices_form_class': FedoraChoiceField}
        else:
            defaults = {'form_class': django.forms.CharField}
        defaults.update(kwargs)

        return wrap_multi_valued_field(self, kwargs, django.db.models.Field, super().formfield(**defaults))

    def get_internal_type(self):
        return None

    def convert_to_rdf(self, value):
        if value is None or not value.strip():
            return []
        return Literal(value, datatype=XSD.string)

    def convert_from_rdf(self, value):
        return str(value)


class IndexedURIRefField(IndexedTextField):

    def convert_to_rdf(self, value):
        if value is None or not value.strip():
            return []
        if isinstance(value, URIRef):
            return value
        return URIRef(value)

    def convert_from_rdf(self, value):
        return str(value)


class IndexedIntegerField(IndexedField, django.db.models.IntegerField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False,
                 attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.IntegerField.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def convert_to_rdf(self, value):
        if value is None:
            return []
        return Literal(value, datatype=XSD.integer)

    def convert_from_rdf(self, value):
        return value.value

    def formfield(self, **kwargs):
        defaults = {}

        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.IntegerField, super().formfield(**defaults))


class IndexedBooleanField(IndexedField, django.db.models.BooleanField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False,
                 attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.IntegerField.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def convert_to_rdf(self, value):
        if value is None:
            return []
        return Literal(value, datatype=XSD.boolean)

    def convert_from_rdf(self, value):
        return value.value

    def formfield(self, **kwargs):
        defaults = {}

        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.BooleanField, super().formfield(**defaults))


class IndexedDateTimeField(IndexedField, django.db.models.DateTimeField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False,
                 attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.DateTimeField.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def convert_to_rdf(self, value):
        if value is None:
            return []
        if isinstance(value, datetime.datetime):
            # check if the datetime is timezone aware
            if value.tzinfo is not None and value.tzinfo.utcoffset(value) is not None:
                return Literal(value, datatype=XSD.datetime)
            else:
                raise TypeError('Required timezone aware datetime because of rdflib ordering issues when mixing naive and tz aware datetimes')
        else:
            raise AttributeError("Conversion of %s to datetime is not supported in "
                                 "fedoralink/indexer/fields.py" % type(value))

    def convert_from_rdf(self, data):
        value = data.toPython()
        if value:
            if isinstance(value, datetime.datetime):
                return value
            print("# TODO:  neskor odstranit")
            if value is "None":         # TODO:  neskor odstranit
                return None
            val = value
            # noinspection PyBroadException
            try:
                # handle 2016-06-03 00:00:00
                if val[-1] != '0':
                    val = datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
                    return val
                # handle 2005-06-08 00:00:00+00:00
                if val[-3] == ':':
                    val = val[:-3] + val[-2:]
                val = datetime.datetime.strptime(val, '%Y-%m-%d %H:%M:%S%z')
                return val
            except:
                # noinspection PyBroadException
                try:
                    if val[-3] == ':':
                        val = val[:-3] + val[-2:]
                    return parser.parse(val)
                except:
                    traceback.print_exc()
                    pass

            raise AttributeError("Conversion of %s [%s] to datetime is not supported in "
                                 "fedoralink/indexer/models.py" % (type(value), value))

    def formfield(self, **kwargs):
        defaults = {}

        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.DateTimeField, super().formfield(**defaults))


class IndexedDateField(IndexedField, django.db.models.DateField):

    def __init__(self, rdf_name, required=False, verbose_name=None, multi_valued=False,
                 attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.DateField.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def convert_to_rdf(self, value):
        if value is None:
            return []
        if isinstance(value, datetime.datetime):
            return Literal(value.date(), datatype=XSD.date)
        elif isinstance(value, datetime.date):
            return Literal(value, datatype=XSD.date)
        else:
            raise AttributeError("Conversion of %s to date is not supported in "
                                 "fedoralink/indexer/fields.py" % type(value))

    def convert_from_rdf(self, data):
        if data.value:
            if isinstance(data.value, datetime.datetime):
                return data.value.date()
            if isinstance(data.value, datetime.date):
                return data.value
            print("# TODO:  neskor odstranit")
            if data.value is "None":      # TODO:  neskor odstranit
                return None
            # noinspection PyBroadException
            try:
                # handle 2005-06-08
                val = data.value
                val = datetime.datetime.strptime(val, '%Y-%m-%d').date()
                return val
            except:
                traceback.print_exc()
                pass

            raise AttributeError("Conversion of %s [%s] to date is not supported in "
                                 "fedoralink/indexer/models.py" % (type(data.value), data.value))

    def formfield(self, **kwargs):
        defaults = {}

        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.DateField, super().formfield(**defaults))


def register_model_lookup(field, related_model):
    if isinstance(related_model, str):
        app_label, model_name = related_model.split('.')
        try:
            field.related_model = apps.get_registered_model(app_label, model_name)
        except LookupError:
            def resolve(**kwargs):
                clz = kwargs['sender']
                # noinspection PyProtectedMember
                if clz._meta.app_label == app_label and clz._meta.object_name == model_name:
                    field.related_model = clz
                    class_prepared.disconnect(resolve, weak=False)

            class_prepared.connect(resolve, weak=False)
    else:
        field.related_model = related_model


def _filter_accessible_references(refs):
    if not refs:
        return refs
    if not isinstance(refs, list) and not isinstance(refs, tuple):
        refs = [refs]
    ret = [
        ref for ref in refs if ref != FEDORA.inaccessibleResource
    ]
    return ret


class IndexedLinkedField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, related_model, required=False, verbose_name=None, multi_valued=False,
                 attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

        register_model_lookup(self, related_model)

    def get_internal_type(self):
        return 'TextField'

    def convert_to_rdf(self, value):
        if value is None:
            return []
        return URIRef(value.id)

    def convert_from_rdf(self, value):
        if not value:
            return None
        return self.related_model.objects.get(pk=value)

    def formfield(self, **kwargs):
        defaults = {'form_class': LinkedField,
                    'model_field': self}

        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.Field, super().formfield(**defaults))

    def instrument(self, model_class, name):
        super().instrument(model_class, name)

        setattr(model_class, '%s__has_references' % name,
                property(lambda inst: True if inst.metadata[self.rdf_name] else False))

        setattr(model_class, '%s__accessible_references' % name,
                property(lambda inst: _filter_accessible_references(inst.metadata[self.rdf_name])))


class IndexedBinaryField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, related_model, required=False, verbose_name=None, multi_valued=False, attrs=None,
                 help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=multi_valued, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

        register_model_lookup(self, related_model)

    def formfield(self, **kwargs):
        # This is a fairly standard way to set up some defaults
        # while letting the caller override them.
        defaults = {'form_class': django.forms.FileField}
        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.Field, super().formfield(**defaults))

    def convert_to_rdf(self, value):
        if value is None:
            return []
        return URIRef(value.id)

    def convert_from_rdf(self, value):
        if not value:
            return None
        return self.related_model.objects.get(pk=value)

    def instrument(self, model_class, name):
        super().instrument(model_class, name)

        setattr(model_class, '%s__has_references' % name,
                property(lambda inst: True if inst.metadata[self.rdf_name] else False))

        setattr(model_class, '%s__accessible_references' % name,
                property(lambda inst: _filter_accessible_references(inst.metadata[self.rdf_name])))


class IndexedGPSField(IndexedField, django.db.models.Field):

    def __init__(self, rdf_name, required=False, verbose_name=None, attrs=None, help_text=None, level=None):
        super().__init__(rdf_name, required=required,
                         verbose_name=verbose_name, multi_valued=False, attrs=attrs, level=level)
        # WHY is Field's constructor not called without this?
        # noinspection PyCallByClass,PyTypeChecker
        django.db.models.Field.__init__(self, verbose_name=verbose_name, help_text=help_text)

    def formfield(self, **kwargs):
        defaults = {'form_class': GPSField}

        defaults.update(kwargs)
        return wrap_multi_valued_field(self, kwargs, django.db.models.Field, super().formfield(**defaults))

    def get_internal_type(self):
        return 'TextField'

    def convert_to_rdf(self, value):
        if value is None or not value.strip():
            return []
        return Literal(value, datatype=XSD.string)

    def convert_from_rdf(self, value):
        return value


def wrap_multi_valued_field(indexed_field, kwargs, django_field_class, ret):
    if indexed_field.multi_valued:
        defaults = {'form_class': MultiValuedFedoraField,
                    'child_field': ret}
        defaults.update(kwargs)
        ret = django_field_class.formfield(indexed_field, **defaults)
    return ret
