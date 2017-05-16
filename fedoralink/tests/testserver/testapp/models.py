from django.db import models

from fedoralink.fedorans import CESNET
from fedoralink.models import fedora


@fedora(namespace=CESNET)
class Simple(models.Model):
    pass