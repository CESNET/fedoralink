from django.db import models

from fedoralink.fedorans import CESNET
from fedoralink.models import fedora
from fedoralink.fields import FedoraField, JSONField


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


@fedora(namespace=CESNET, rdf_types=[CESNET.all_field_types])
class BasicFieldTypes(models.Model):
    char_field = models.CharField(max_length=20)
    text_field = models.TextField()
    slug_field = models.SlugField()
    url_field = models.URLField()
    uuid_field = models.UUIDField()

    int_field = models.IntegerField()
    biginteger_field = models.BigIntegerField()
    positive_integer_field = models.PositiveIntegerField()
    positive_small_integer_field = models.PositiveSmallIntegerField()
    small_integer_field = models.SmallIntegerField()

    float_field = models.FloatField()
    decimal_field = models.DecimalField(decimal_places=2, max_digits=1000)

    date_field = models.DateField()
    time_field = models.TimeField()
    datetime_field = models.DateTimeField()
    duration_field = models.DurationField()

    ip_field = models.GenericIPAddressField()

    email = models.EmailField()

    boolean_field = models.BooleanField()
    null_boolean = models.NullBooleanField()


@fedora(namespace=CESNET, rdf_types=[CESNET.binary_field_types])
class BinaryFieldTypes(models.Model):
    binary_field = models.BinaryField()
    file = models.FileField()
    image = models.ImageField()


@fedora(namespace=CESNET, rdf_types=[CESNET.foreign])
class ModelWithForeignKey(models.Model):
    f = models.ForeignKey(Simple, on_delete=models.SET_NULL, null=True, blank=True)


@fedora(namespace=CESNET, rdf_types=[CESNET.foreign2])
class ModelWithTwoForeignKeys(models.Model):
    f = models.ForeignKey(Simple, related_name='+', on_delete=models.SET_NULL, null=True, blank=True)
    g = models.ForeignKey(Simple, related_name='+', on_delete=models.SET_NULL, null=True, blank=True)


@fedora(namespace=CESNET, rdf_types=[CESNET.foreign_many])
class ModelWithForeignKeyArray(models.Model):
    f = FedoraField(models.ForeignKey(Simple, on_delete=models.SET_NULL, null=True, blank=True),
                    multiplicity=FedoraField.ANY)


@fedora(namespace=CESNET, rdf_types=[CESNET.json])
class JsonModel(models.Model):
    json_single = JSONField(null=True, blank=True)
    json_multiple = FedoraField(JSONField(null=True, blank=True), multiplicity=FedoraField.ANY)

