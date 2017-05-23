import logging
import traceback

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils import FieldTracker

from fedoralink.db.utils import rdf2search
from fedoralink.fedora_meta import FedoraOptions
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
                          explicitly_declared=True, default_parent=default_parent)

        fld = FedoraResourceUrlField(null=True, blank=True, verbose_name=_('Fedora resource URL'))
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
