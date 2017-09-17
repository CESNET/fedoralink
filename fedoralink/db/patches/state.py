import django.db.models
from django.db.migrations import CreateModel, AddField

from fedoralink.migration_ops import FedoraCreateModel, FedoraAddField

import logging

log = logging.getLogger('fedoralink.patches.state')

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
            if model._meta.fedora_options.explicitly_declared and ret.bases != (django.db.models.Model,):
                # if the class was explicitly declared to be stored in fedora
                # and there is inheritance, remove it - it has already been
                # flattened
                ret.bases = (django.db.models.Model,)
        return ret

    ModelState.from_model = from_model

    previous_migrationautodetector_changes = MigrationAutodetector.changes

    def changes(self, graph, trim_to_apps=None, convert_apps=None, migration_name=None):
        ret = previous_migrationautodetector_changes(self, graph, trim_to_apps, convert_apps, migration_name)
        print(ret)
        for app_name, migrations in ret.items():
            for migration in migrations:
                for idx, operation in list(enumerate(migration.operations)):
                    if isinstance(operation, CreateModel):
                        model_state = self.to_state.models[(migration.app_label, operation.name_lower)]
                        if not hasattr(model_state, 'fedora_options'):
                            continue
                        operation = FedoraCreateModel.duplicate(operation, model_state.fedora_options)
                        migration.operations[idx] = operation
                    if isinstance(operation, AddField):
                        from django.apps import apps
                        try:
                            current_model = apps.get_model(app_name, operation.model_name)
                            current_field = getattr(current_model, operation.name, None).field
                        except:
                            # no model for that field or the field looks different, maybe removed?
                            log.error('No model for field or removed?', app_name, operation.model_name)
                            continue

                        if not hasattr(current_field, 'fedora_options'):
                            continue

                        operation = FedoraAddField.duplicate(operation, {
                            'rdf_namespace': str(current_field.fedora_options.rdf_namespace),
                            'rdf_name': str(current_field.fedora_options.rdf_name),
                            'model': {
                                'primary_rdf_type': str(current_model._meta.fedora_options.primary_rdf_type),
                                'rdf_namespace':    str(current_model._meta.fedora_options.rdf_namespace),
                                'rdf_types':        [str(x) for x in current_model._meta.fedora_options.rdf_types],
                                'field_options':    current_model._meta.fedora_options.field_options,
                                'default_parent':   current_model._meta.fedora_options.default_parent,
                            }
                        })
                        migration.operations[idx] = operation
        return ret

    MigrationAutodetector.changes = changes
