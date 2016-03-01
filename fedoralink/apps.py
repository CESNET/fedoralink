# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


def do_index(sender, **kwargs):

    from fedoralink.models import IndexableFedoraObject
    from django.db import connections
    from django.conf import settings

    instance = kwargs['instance']
    db = kwargs['using']

    print("do_index called", db, instance, settings.DATABASES[db].get('USE_INTERNAL_INDEXER', False))

    if settings.DATABASES[db].get('USE_INTERNAL_INDEXER', False) and isinstance(instance, IndexableFedoraObject):
        print("Running indexer")
        indexer = connections[db].indexer
        indexer.reindex(instance)


def upload_binary_files(sender, **kwargs):

    from fedoralink.models import fedoralink_clear_streams, UploadedFileStream
    from django.core.files.uploadedfile import UploadedFile
    from fedoralink.utils import TypedStream
    from rdflib import URIRef

    instance = kwargs['instance']

    save_required = False
    from fedoralink.models import fedoralink_streams
    for fld, streams in fedoralink_streams(instance):
        ids = []
        print(type(streams))
        for stream_id, stream in enumerate(streams):

            if isinstance(stream, UploadedFile):
                stream = TypedStream(UploadedFileStream(stream), stream.content_type, stream.name)

            stream_inst = instance.create_child("%s_%s" % (fld.name, stream_id))
            stream_inst.set_local_bitstream(stream)
            stream_inst.save()
            ids.append(URIRef(stream_inst.id))

        setattr(instance, fld.name, ids)
        save_required = True

    if save_required:
        fedoralink_clear_streams(instance)
        instance.save()


class ApplicationConfig(AppConfig):
    name = 'fedoralink'
    verbose_name = _("fedoralink")

    def ready(self):
        super().ready()

        from django.db.models.signals import post_save

        post_save.connect(do_index, dispatch_uid='indexer', weak=False)
        post_save.connect(upload_binary_files, dispatch_uid='upload_binary_files', weak=False)