from django.contrib.postgres.fields import ArrayField
from django.db.models import TextField
from rdflib import Literal, URIRef

from fedoralink.fedora_meta import FedoraFieldOptions


class GenericFedoraField(TextField):
    def __init__(self, model, rdf_name):
        super().__init__(null=True, blank=True)
        self.set_attributes_from_name(rdf_name)
        self.model = model
        self.fedora_options = FedoraFieldOptions(field=self, rdf_name=rdf_name)


class FedoraArrayField(ArrayField):
    """
     Field in fedora can be an array of values, similarly to Postgresql's field.
     That's why this class inherits somewhat illogically from postgres ArrayField.
     Please do not count on it as it might change in the future.
    """
    def __init__(self, base_field, size=None,
                 rdf_namespace=None, rdf_name=None,
                 **kwargs):
        self.fedora_options = FedoraFieldOptions(field=self, rdf_namespace=rdf_namespace, rdf_name=rdf_name)
        super().__init__(base_field, size, **kwargs)

    def to_python(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            ret = []
            for val in value:
                ret.append(self.base_field.to_python(val))
            value = ret
        return value
