__author__ = 'simek'


class FedoraRouter(object):

    def db_for_read(self, model, **hints):
        if hasattr(model._meta, 'fedora_options') and model._meta.fedora_options.explicitly_declared:
            return 'repository'
        return None

    def db_for_write(self, model, **hints):
        if hasattr(model._meta, 'fedora_options') and model._meta.fedora_options.explicitly_declared:
            return 'repository'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        obj1_in_repository = hasattr(obj1._meta, 'fedora_options') and obj1._meta.fedora_options.explicitly_declared
        obj2_in_repository = hasattr(obj2._meta, 'fedora_options') and obj2._meta.fedora_options.explicitly_declared

        if obj1_in_repository and obj2_in_repository:
            return True

        if obj1_in_repository ^ obj2_in_repository:
            return False

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if 'model' in hints:
            model = hints['model']
            if hasattr(model._meta, 'fedora_options') and model._meta.fedora_options.explicitly_declared:
                return db == 'repository'
        return None
