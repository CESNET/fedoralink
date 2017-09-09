import copy
import logging

from django.db import models
from django.db.models import OneToOneField
from django.db.models.signals import post_init
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from model_utils import FieldTracker

from fedoralink.db.rdf import RDFMetadata
from fedoralink.fedora_meta import FedoraOptions
from fedoralink.manager import FedoraManager

log = logging.getLogger('fedoralink.models')


class FedoraResourceUrlField(models.TextField):
    pass


def fedora(namespace=None, rdf_types=None, field_options=None, primary_rdf_type=None, default_parent=None):
    def annotate(clz):
        clz._meta.fedora_options = \
            FedoraOptions(clz, rdf_namespace=namespace, rdf_types=rdf_types,
                          primary_rdf_type=primary_rdf_type, field_options=field_options,
                          explicitly_declared=True, default_parent=default_parent, used_from_decorator=True)

        inherited = not not clz._meta.parents

        # make pycharm happy
        tracker_fld = None

        if not inherited:
            fld = FedoraResourceUrlField(null=True, blank=True, unique=True, verbose_name=_('Fedora resource URL'))
            fld.contribute_to_class(clz, 'fedora_id')

            # add FieldTracker field
            tracker_fld = FieldTracker()
            tracker_fld.contribute_to_class(clz, 'fedora_field_tracker')

        # replace manager with FedoraManager
        manager = FedoraManager()
        clz._meta.local_managers.clear()
        manager.contribute_to_class(clz, 'objects')
        clz._meta.base_manager = manager

        # class_prepared signal has already been sent, so emit it again just for the FieldTracker

        if not inherited:
            tracker_fld.finalize_class(clz)

        def invalidate(obj):
            for key, value in obj.__class__.__dict__.items():
                if isinstance(value, cached_property):
                    obj.__dict__.pop(key, None)

        if inherited:
            pk_field = None
            options = clz._meta
            # remove the reference to the parent class(es) from fields, as we need to serialize the whole
            # content to one fedora object
            for parent_class in options.parents.keys():
                if parent_class == clz:
                    continue
                if not hasattr(parent_class, 'fedora_id'):
                    continue
                for fld in options.fields:
                    if isinstance(fld, OneToOneField) and 'self' in fld.from_fields:
                        if fld.target_field == parent_class._meta.pk:
                            # found the linking field, remove it ...
                            pk_field = fld.target_field
                            options.local_fields.remove(fld)
                            options._expire_cache()
                            options._expire_cache(True)
                            invalidate(options)
                            break


            # change the pk field back to the original id
            options.pk = pk_field

            # copy all fields to local fields
            for parent_class in options.parents.keys():
                for fld in parent_class._meta.local_fields:
                    if fld not in options.local_fields:
                        fld = copy.copy(fld)
                        fld.contribute_to_class(clz, fld.name)

            # remove parents
            options.parents.clear()
            options._expire_cache()
            options._expire_cache(True)
            invalidate(options)

        return clz

    return annotate


@fedora()
class FedoraObject(models.Model):
    pass


@fedora()
class BinaryObject(models.Model):
    pass


def _on_fedora_post_init(sender, **kwargs):
    if hasattr(sender._meta, 'fedora_options') and not hasattr(sender, 'fedora_meta'):
        # create empty metadata
        sender.fedora_meta = RDFMetadata('')


post_init.connect(_on_fedora_post_init)
