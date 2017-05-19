from django.db import models

from fedoralink.fedorans import CESNET
from fedoralink.models import fedora


@fedora(namespace=CESNET)
class Simple(models.Model):
    text = models.TextField(null=True, blank=True)


@fedora(namespace=CESNET)
class Complex(models.Model):
    a = models.CharField(max_length=10)
    b = models.CharField(max_length=10)