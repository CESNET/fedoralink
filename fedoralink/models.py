import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from fedoralink.db.utils import rdf2search
from fedoralink.fedora_meta import FedoraOptions
from fedoralink.fedorans import CESNET, CESNET_TYPE
from fedoralink.manager import FedoraManager

log = logging.getLogger('fedoralink.models')


class FedoraResourceUrlField(models.TextField):
    pass


def fedora(namespace=None, rdf_types=None, field_options=None):
    def annotate(clz):
        clz._meta.fedora_options = \
            FedoraOptions(clz, rdf_namespace=namespace, rdf_types=rdf_types, field_options=field_options,
                          explicitly_declared=True)

        fld = FedoraResourceUrlField(null=True, blank=True, verbose_name=_('Fedora resource URL'))
        fld.contribute_to_class(clz, 'fedora_id')

        # replace manager with FedoraManager
        manager = FedoraManager()
        clz._meta.local_managers.clear()
        manager.contribute_to_class(clz, 'objects')

        # TODO: implement metadata and children
        # fld = models.CharField(required=False, verbose_name=_('Fedora metadata'))
        # fld.contribute_to_class(clz, 'fedora_meta')
        #
        # fld = models.CharField(required=False, verbose_name=_('Resource children'))
        # fld.contribute_to_class(clz, 'fedora_children')
        return clz
    return annotate


@fedora()
class FedoraObject(models.Model):
    pass
