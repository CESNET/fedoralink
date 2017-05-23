from django.db.migrations import CreateModel
from rdflib import Namespace, URIRef


class FedoraCreateModel(CreateModel):

    def __init__(self, name, fields, options=None, bases=None, managers=None, fedora_options=None):
        super().__init__(name=name, fields=fields, options=options, bases=bases, managers=managers)
        self.fedora_options = fedora_options

    @classmethod
    def duplicate(cls, operation, fedora_options):
        ret = FedoraCreateModel(operation.name, operation.fields, operation.options, operation.bases, operation.managers,
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