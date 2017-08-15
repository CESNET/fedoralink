from django.core.files import File
from django.core.files.storage import Storage
from django.db import connections
from django.utils.deconstruct import deconstructible
from rdflib import Literal, XSD

from fedoralink.fedorans import EBUCORE


@deconstructible
class FedoraStorage(Storage):
    def __init__(self, repository_name="repository"):
        """
        Initializes a new storage for Fedora binary resources.

        :param repository_name: the database to use
        """
        self.repository_name = repository_name

    def _open(self, name, mode='rb'):
        from fedoralink.models import FedoraObject
        fo = FedoraObject.objects

        if self.repository_name:
            conn = connections[self.repository_name]
            fo = fo.using(self.repository_name)
        else:
            conn = connections['repository']

        fo = fo.get(fedora_id=name)
        return FedoraBinaryStream(fo, name, conn)

    def _save(self, name, content):
        from fedoralink.models import BinaryObject
        fo = BinaryObject()
        fo.fedora_meta[EBUCORE.filename] = Literal(content.name, datatype=XSD.string)
        content_type = getattr(content, 'content_type', None)
        if content_type:
            fo.fedora_meta[EBUCORE.hasMimeType] = Literal(content_type, datatype=XSD.string)
        fo.fedora_meta[EBUCORE.hasSize] = Literal(content.size, datatype=XSD.integer)
        fo.fedora_binary_stream = content
        fo.save(using=self.repository_name)
        return fo.fedora_id

    def delete(self, name):
        raise NotImplementedError("Not implemented")

    def exists(self, name):
        if name.startswith('http://') or name.startswith('https://'):
            raise Exception('Lookup to repository to check for name existence is not yet implemented')
        return False

    def get_accessed_time(self, name):
        raise NotImplementedError("Not implemented")

    def get_created_time(self, name):
        raise NotImplementedError("Not implemented")

    def get_modified_time(self, name):
        raise NotImplementedError("Not implemented")

    def generate_filename(self, filename):
        return super().generate_filename(filename)

    def listdir(self, path):
        raise NotImplementedError("Not implemented")

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        raise NotImplementedError('subclasses of Storage must provide a size() method')

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a Web browser.
        """
        raise NotImplementedError('subclasses of Storage must provide a url() method')


class FedoraBinaryStream(File):
    def __init__(self, fedora_object, name, connection):
        super().__init__(None, name)
        self.fedora_object = fedora_object
        self._connection   = connection
        self.file          = None

    def read(self, chunk_size):
        if not self.file:
            self.open()
        return self.file.read(chunk_size)

    def open(self, mode=None):
        with self._connection.cursor() as cursor:
            self.file = cursor.cursor.connection.fetch_bitstream(self.name)
            return self.file
