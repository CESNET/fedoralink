from django.core.exceptions import FieldError
from django.db.models import QuerySet, sql, CharField, TextField
from django.db.models.manager import BaseManager

from fedoralink.fedora_meta import FedoraFieldOptions


class GenericFedoraField(TextField):
    def __init__(self, model, rdf_name):
        super().__init__(null=True, blank=True)
        self.set_attributes_from_name(rdf_name)
        self.model = model
        self.fedora_options = FedoraFieldOptions(field=self, rdf_name=rdf_name)


class FedoraQuery(sql.Query):
    def names_to_path(self, names, opts, allow_many=True, fail_on_missing=False):
        try:
            # use normal resolving if possible
            return super().names_to_path(names, opts, allow_many, fail_on_missing)
        except FieldError:
            pass

        # if not possible, create a new field and return it
        name = names[0]

        field = GenericFedoraField(opts.model, name)
        targets = (field,)

        # path, final_field, targets, extra data after __ (lookups & transforms)
        return [], field, targets, names[1:]


class FedoraQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        if not query:
            query = FedoraQuery(model)
        super().__init__(model, query, using, hints)


class FedoraManager(BaseManager.from_queryset(FedoraQuerySet)):
    pass
