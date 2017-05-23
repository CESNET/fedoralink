from django.db.migrations import CreateModel

from fedoralink.migration_ops import FedoraCreateModel


def patch_model_state_from_model():
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.state import ModelState

    previous_from_model = ModelState.from_model

    def from_model(model, exclude_rels=False):
        ret = previous_from_model(model, exclude_rels)
        if hasattr(model._meta, 'fedora_options'):
            ret.fedora_options = {
                'primary_rdf_type': str(model._meta.fedora_options.primary_rdf_type),
                'rdf_namespace':    str(model._meta.fedora_options.rdf_namespace),
                'rdf_types':        [str(x) for x in model._meta.fedora_options.rdf_types],
                'field_options':    model._meta.fedora_options.field_options,
                'default_parent':   model._meta.fedora_options.default_parent,
            }
        return ret

    ModelState.from_model = from_model

    previous_migrationautodetector_changes = MigrationAutodetector.changes

    def changes(self, graph, trim_to_apps=None, convert_apps=None, migration_name=None):
        ret = previous_migrationautodetector_changes(self, graph, trim_to_apps, convert_apps, migration_name)
        print(ret)
        for app_name, migrations in ret.items():
            for migration in migrations:
                for idx, operation in list(enumerate(migration.operations)):
                    if not isinstance(operation, CreateModel):
                        continue
                    model_state = self.to_state.models[(migration.app_label, operation.name_lower)]
                    if not hasattr(model_state, 'fedora_options'):
                        continue
                    operation = FedoraCreateModel.duplicate(operation, model_state.fedora_options)
                    migration.operations[idx] = operation
        return ret

    MigrationAutodetector.changes = changes
