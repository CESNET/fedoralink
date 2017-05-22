
def patch_save(sender, instance, **kwargs):
    original_save = instance.save

    def save(**kwargs):
        if not kwargs.get('update_fields', None) and instance.pk:
            print(instance)
            if hasattr(instance, 'fedora_field_tracker'):
                changed = instance.fedora_field_tracker.changed()
                kwargs['update_fields'] = list(changed.keys())
        return original_save(**kwargs)

    orig_do_update = instance._do_update

    def _do_update(base_qs, using, pk_val, values, update_fields, forced_update):
        if hasattr(instance, 'fedora_field_tracker'):
            base_qs = base_qs.set_patch_previous_data(dict(instance.fedora_field_tracker.changed()))
            base_qs = base_qs.set_patched_instance(instance)
        return orig_do_update(base_qs, using, pk_val, values, update_fields, forced_update)

    instance.save = save
    instance._do_update = _do_update