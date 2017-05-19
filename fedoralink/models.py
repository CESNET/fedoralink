import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from fedoralink.db.utils import rdf2search
from fedoralink.fedorans import CESNET

log = logging.getLogger('fedoralink.models')


class FedoraResourceUrlField(models.TextField):
    pass


class FedoraFieldOptions:

    def __init__(self, field=None, rdf_namespace=None, rdf_name=None):
        self.field = field
        if rdf_name:
            self.rdf_name = rdf_name
        else:
            if not self.field:
                raise AttributeError('Please use rdf_name in FedoraFieldOptions constructor')
            self.rdf_name = getattr(rdf_namespace, self.field.name)

        self.search_name = rdf2search(self.rdf_name)


class FedoraOptions:

    def __init__(self, clz, rdf_namespace=None, rdf_types=None, field_options=None, explicitly_declared=False):
        self.clz           = clz
        self.rdf_namespace = rdf_namespace
        self.explicitly_declared = explicitly_declared
        if not self.rdf_namespace:
            self.rdf_namespace = CESNET
        self.rdf_types     = rdf_types

        for parent in clz._meta.parents:
            if not hasattr(parent, '_meta'):
                continue
            if not hasattr(parent._meta, 'fedora_options'):
                FedoraOptions(parent, self.rdf_namespace)

        if not self.rdf_types:
            self.rdf_types = [
                getattr(self.rdf_namespace, clz._meta.db_table)
            ]

        for fld in clz._meta.fields:
            if not hasattr(fld, 'fedora_options'):
                if field_options and fld.name in field_options:
                    fld.fedora_options = field_options[fld.name]
                    fld.fedora_options.field = fld
                else:
                    fld.fedora_options = FedoraFieldOptions(field=fld, rdf_namespace=self.rdf_namespace)


def fedora(namespace=None, rdf_types=None, field_options=None):
    def annotate(clz):
        clz._meta.fedora_options = \
            FedoraOptions(clz, rdf_namespace=namespace, rdf_types=rdf_types, field_options=field_options,
                          explicitly_declared=True)

        fld = FedoraResourceUrlField(null=True, blank=True, verbose_name=_('Fedora resource URL'))
        fld.contribute_to_class(clz, 'fedora_id')

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
