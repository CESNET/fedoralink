# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from fedoralink.idmapping import id2url


def upload_binary_files(sender, **kwargs):
    pass
    # from fedoralink.models import UploadedFileStream
    # from fedoralink.indexer.models import fedoralink_clear_streams
    # from django.core.files.uploadedfile import UploadedFile
    # from fedoralink.utils import TypedStream
    #
    # instance = kwargs['instance']
    #
    # save_required = False
    # from fedoralink.indexer.models import fedoralink_streams
    # for fld, streams in fedoralink_streams(instance):
    #     stream_instances = []
    #     # print(type(streams))
    #     for stream_id, stream in enumerate(streams):
    #
    #         if isinstance(stream, UploadedFile):
    #             stream = TypedStream(UploadedFileStream(stream), stream.content_type, stream.name)
    #
    #         stream_inst = instance.create_child("%s_%s" % (fld.name, stream_id))
    #         stream_inst.set_local_bitstream(stream)
    #         stream_inst.save()
    #         stream_instances.append(stream_inst)
    #
    #     setattr(instance, fld.name, stream_instances)
    #     save_required = True
    #
    # if save_required:
    #     fedoralink_clear_streams(instance)
    #     instance.save()


def fix_fedora_id(sender, **kwargs):
    inst = kwargs['instance']
    created = kwargs['created']
    if not created:
        return              # URI does not change on updates ...
    if hasattr(sender._meta, 'fedora_options'):
        inst.fedora_id = id2url(inst.id)


class ApplicationConfig(AppConfig):
    name = 'fedoralink'
    verbose_name = _("fedoralink")

    def ready(self):
        super().ready()

        # make sure common namespaces are loaded
        # noinspection PyUnresolvedReferences
        # TODO: import fedoralink.common_namespaces.dc

        # noinspection PyUnresolvedReferences
        # TODO: import fedoralink.common_namespaces.web_acl.models

        from django.db.models.signals import post_save

        post_save.connect(upload_binary_files, dispatch_uid='upload_binary_files', weak=False)

        from fedoralink.db.lookups import add_vendor_to_lookups
        add_vendor_to_lookups()

        from django.db.models.signals import post_save
        post_save.connect(fix_fedora_id, dispatch_uid='fix_fedora_id', weak=False)