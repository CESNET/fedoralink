import logging
import traceback

from django.db import models
from django.db.models import TextField, CharField, ForeignKey, BinaryField
from django.db.models.signals import post_init
from django.utils.translation import ugettext_lazy as _
from model_utils import FieldTracker

from fedoralink.db.rdf import RDFMetadata
from fedoralink.db.utils import rdf2search
from fedoralink.fedora_meta import FedoraOptions, FedoraFieldOptions
from fedoralink.fedorans import CESNET, CESNET_TYPE
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

        # TODO: implement children
        # fld = models.CharField(required=False, verbose_name=_('Fedora metadata'))
        # fld.contribute_to_class(clz, 'fedora_meta')
        #
        # fld = models.CharField(required=False, verbose_name=_('Resource children'))
        # fld.contribute_to_class(clz, 'fedora_children')

        # class_prepared signal has already been sent, so emit it again just for the FieldTracker

        tracker_fld.finalize_class(clz)

        return clz
    return annotate


@fedora()
class FedoraObject(models.Model):
    pass


@fedora(namespace=CESNET_TYPE, rdf_types=(CESNET_TYPE.Template,))
#TODO: how to set field options here???        field_options={'label': FedoraFieldOptions(label, rdf_types=CESNET_TYPE.label),...})
class Template(models.Model):
    label = TextField(verbose_name=_('Label'))
    tags = TextField(verbose_name=_('Tags'))
    data = BinaryField(verbose_name=_('Template data'), null=True)


@fedora(namespace=CESNET_TYPE, rdf_types=(CESNET_TYPE.ResourceType,))
#TODO: how to set field options here???        field_options={'label': FedoraFieldOptions(label, rdf_types=CESNET_TYPE.label),...})
class ResourceType(models.Model):
    label = TextField(verbose_name=_('Label'))

    template_view = ForeignKey(Template, to_field='fedora_id', verbose_name=_('Template for view'),
                               related_name='template_view', null=True, on_delete=models.SET_NULL)
    template_edit = ForeignKey(Template, to_field='fedora_id', verbose_name=_('Template for edit'),
                               related_name='template_edit', null=True, on_delete=models.SET_NULL)
    template_list_item = ForeignKey(Template, to_field='fedora_id', verbose_name=_('Template for item list view'),
                                    related_name='template_list', null=True, on_delete=models.SET_NULL)

    controller = TextField(verbose_name=_('Controller class'))
    rdf_types = TextField(verbose_name=_('RDF types'))

    # TODO: Migrate metadata app from oarepo to fedoralink??? Until then, just use a Fedora resource uri
    # model_description = models.ForeignKey('MetadataDescription', verbose_name=_('Model metadata description'))
    model_description = CharField(verbose_name=_('Model metadata description'), max_length=2048)

@fedora()
class BinaryObject(models.Model):
    pass

def _on_fedora_post_init(sender, **kwargs):
    if hasattr(sender._meta, 'fedora_options') and not hasattr(sender, 'fedora_meta'):
        # create empty metadata
        sender.fedora_meta = RDFMetadata('')

post_init.connect(_on_fedora_post_init)
