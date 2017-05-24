import numbers
from enum import Enum

from django.core.exceptions import FieldError
from django.db.models import QuerySet, sql, CharField, TextField
from django.db.models.manager import BaseManager
from django.db.models.sql import UpdateQuery
from rdflib import URIRef

from fedoralink.db.lookups import FedoraMetadataAnnotation
from fedoralink.fedora_meta import FedoraFieldOptions
from fedoralink.idmapping import url2id

# constants to be used in FedoraObject.objects.via(...) call
FEDORA_REPOSITORY    = 1
ELASTICSEARCH        = 2


class GenericFedoraField(TextField):
    def __init__(self, model, rdf_name):
        super().__init__(null=True, blank=True)
        self.set_attributes_from_name(rdf_name)
        self.model = model
        self.fedora_options = FedoraFieldOptions(field=self, rdf_name=rdf_name)


class DjangoMetaProxy:
    def __init__(self, meta):
        object.__setattr__(self, "_proxied_meta", meta)
        self._proxied_meta = meta

    def __getattribute__(self, item):
        try:
            return object.__getattribute__(self, item)
        except:
            pass
        print("meta proxy getattr", item)
        return getattr(object.__getattribute__(self, '_proxied_meta'), item)

    def __setattr__(self, key, value):
        print("meta proxy setattr", key, value)
        return setattr(object.__getattribute__(self, '_proxied_meta'), key, value)

    def get_field(self, field_name):
        if isinstance(field_name, URIRef):
            return GenericFedoraField(self.model, field_name)
        return getattr(object.__getattribute__(self, '_proxied_meta'), 'get_field')(field_name)


class PatchedUpdateQuery(UpdateQuery):

    def get_meta(self):
        return DjangoMetaProxy(super().get_meta())


class FedoraQuery(sql.Query):

    def __init__(self, model):
        super().__init__(model)
        self.fedora_via = None
        self.previous_update_values = None
        self.patched_instance = None

    def names_to_path(self, names, opts, allow_many=True, fail_on_missing=False):
        try:
            # use normal resolving if possible
            return super().names_to_path(names, opts, allow_many, fail_on_missing)
        except FieldError:
            pass

        # if not possible, create a new field and return it
        name = names[0]

        field = GenericFedoraField(opts.model, name)
        targets = (field,)

        # path, final_field, targets, extra data after __ (lookups & transforms)
        return [], field, targets, names[1:]

    def clone(self, klass=None, memo=None, **kwargs):
        if klass is UpdateQuery:
            klass = PatchedUpdateQuery
        ret = super().clone(klass, memo, **kwargs)
        ret.fedora_via = self.fedora_via
        ret.previous_update_values = self.previous_update_values
        ret.patched_instance = self.patched_instance
        return ret


class FedoraQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        if not query:
            query = FedoraQuery(model)
        super().__init__(model, query, using, hints)

    def get(self, *args, **kwargs):
        if 'pk' in kwargs and not isinstance(kwargs['pk'], numbers.Number):
            kwargs['pk'] = url2id(kwargs['pk'])
        if 'id' in kwargs and not isinstance(kwargs['id'], numbers.Number):
            kwargs['id'] = url2id(kwargs['id'])
        return super().get(*args, **kwargs)

    def via(self, _via):
        """
        When performing pk searches (FedoraObject.objects.filter(pk=...)) the ``via`` decides if the data are
        retrieved from elasticsearch (faster, but some metadata will not be present) or from Fedora Repository
        (safer, the default setting). Use ``FEDORA`` or ``ELASTICSEARCH`` to switch between the two.
        
        :param _via:    either FEDORA or ELASTICSEARCH
        :return:        new QuerySet instance with filled via
        """
        clone = self._clone()
        clone.query.fedora_via = _via
        return clone

    def set_patch_previous_data(self, previous_update_values):
        clone = self._clone()
        clone.query.previous_update_values = previous_update_values
        return clone

    def set_patched_instance(self, patched_instance):
        clone = self._clone()
        clone.query.patched_instance = patched_instance
        return clone



class FedoraManager(BaseManager.from_queryset(FedoraQuerySet)):
    pass

    def get_queryset(self):
        return super().get_queryset().annotate(fedora_meta=FedoraMetadataAnnotation())
