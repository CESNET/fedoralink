# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from rdflib import URIRef

from fedoralink.idmapping import id2url


def upload_binary_files(sender, **kwargs):
    """
    Helper method that sits on the post_save signal to save the binary content of a resource
    
    TODO: not implemented yet !!! 
    """
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
    """
     A helper method sitting on :py:obj:`django.db.models.signals.post_save` that is responsible for setting up 
     the fedora_id field after the resource
     has been created. The fedora_id is the url path of the resource in Fedora Repository and being a string, it can
     not be put directly into Django's AutoField. After .save(), django can retrieve only the pk, which in case of 
     fedoralink is the real url serialized into a big integer. This method takes this integer, runs it through id2url 
     and puts the resulting string into inst.fedora_id
    """
    inst = kwargs['instance']
    created = kwargs['created']
    if not created:
        return              # URI does not change on updates ...
    if hasattr(sender._meta, 'fedora_options'):
        inst.fedora_id = URIRef(id2url(inst.id))


class ApplicationConfig(AppConfig):
    """
        Application config for fedoralink
    """
    name = 'fedoralink'
    verbose_name = _("fedoralink")

    def ready(self):
        """
        Called after the apps have been loaded. Sets up handlers for uploading binary content to Fedora repository,
        connects the :func:`fix_fedora_id` hook and finally adds fedoralink vendor to various django lookup functions (
        such as __exact etc.). For details see :func:`fedoralink.db.lookups.add_vendor_to_lookups`
        """
        super().ready()

        from django.db.models.signals import post_save

        post_save.connect(upload_binary_files, dispatch_uid='upload_binary_files', weak=False)

        from fedoralink.db.lookups import add_vendor_to_lookups
        add_vendor_to_lookups()

        from django.db.models.signals import post_save
        post_save.connect(fix_fedora_id, dispatch_uid='fix_fedora_id', weak=False)