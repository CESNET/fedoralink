__author__ = 'simek'


class FedoraRouter(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label in ('testapp', ):
            return 'repository'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in ('testapp'):
            return 'repository'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        obj1_in_repository = obj1._meta.app_label in ('testapp',)
        obj2_in_repository = obj2._meta.app_label in ('testapp',)

        if obj1_in_repository and obj2_in_repository:
            return True

        if obj1_in_repository ^ obj2_in_repository:
            return False

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in ('testapp', ):
            return db == 'repository'

        return None
