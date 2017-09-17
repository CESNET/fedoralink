from django.db.migrations import CreateModel, AddField
from rdflib import Namespace, URIRef

from fedoralink.fedora_meta import FedoraFieldOptions


class FedoraCreateModel(CreateModel):
    def __init__(self, name, fields, options=None, bases=None, managers=None, fedora_options=None):
        super().__init__(name=name, fields=fields, options=options, bases=bases, managers=managers)
        self.fedora_options = fedora_options

    @classmethod
    def duplicate(cls, operation, fedora_options):
        ret = FedoraCreateModel(operation.name, operation.fields, operation.options, operation.bases,
                                operation.managers,
                                fedora_options)
        return ret

    def deconstruct(self):
        ret = super().deconstruct()
        if self.fedora_options:
            ret[2]['fedora_options'] = self.fedora_options
        return ret

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from fedoralink.models import fedora
        model = to_state.apps.get_model(app_label, self.name)
        # add fedora options to the model
        fedora(namespace=Namespace(self.fedora_options['rdf_namespace']),
               rdf_types=[URIRef(x) for x in self.fedora_options['rdf_types']],
               field_options=self.fedora_options['field_options'],
               primary_rdf_type=URIRef(self.fedora_options['primary_rdf_type']),
               default_parent=self.fedora_options['default_parent'])(model)
        ret = super().database_forwards(app_label=app_label, schema_editor=schema_editor,
                                        from_state=from_state, to_state=to_state)
        return ret


class FedoraAddField(AddField):
    def __init__(self, model_name, name, field, preserve_default=True, fedora_options=None):
        super().__init__(model_name, name, field, preserve_default)
        self.fedora_options = fedora_options

    @classmethod
    def duplicate(cls, operation, fedora_options):
        ret = FedoraAddField(operation.model_name, operation.name,
                             operation.field, operation.preserve_default, fedora_options)
        return ret

    def deconstruct(self):
        ret = super().deconstruct()
        if self.fedora_options:
            ret[2]['fedora_options'] = self.fedora_options
        return ret

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        from fedoralink.models import fedora

        to_model = to_state.apps.get_model(app_label, self.model_name)
        if self.allow_migrate_model(schema_editor.connection.alias, to_model):
            field = to_model._meta.get_field(self.name)
            model_options = self.fedora_options['model']
            fedora(namespace=Namespace(model_options['rdf_namespace']),
                   rdf_types=[URIRef(x) for x in model_options['rdf_types']],
                   field_options=model_options['field_options'],
                   primary_rdf_type=URIRef(model_options['primary_rdf_type']),
                   default_parent=model_options['default_parent'])(to_model)
            field.fedora_options = FedoraFieldOptions(field=field,
                                                      rdf_namespace=self.fedora_options['rdf_namespace'],
                                                      rdf_name=self.fedora_options['rdf_name'])

        ret = super().database_forwards(app_label=app_label, schema_editor=schema_editor,
                                        from_state=from_state, to_state=to_state)
        return ret
