from django.db import models

from fedoralink.fedorans import CESNET
from fedoralink.models import fedora
from fedoralink.fields import FedoraField


@fedora(namespace=CESNET)
class Simple(models.Model):
    text = models.TextField(null=True, blank=True)


@fedora(namespace=CESNET, rdf_types=[CESNET.complex_type])
class Complex(models.Model):
    a = models.CharField(max_length=10)
    b = models.CharField(max_length=10)

@fedora(namespace=CESNET, rdf_types=[CESNET.array_field_test])
class ArrayFieldModel(models.Model):
    a = FedoraField(models.CharField, max_length=10, multiplicity=FedoraField.ANY)