############
Architecture
############

Fedoralink consists of the following parts:

1. Authentization middleware to pass django user and groups to fedora repository via standard ``On-Behalf-Of``
   and proprietary ``On-Behalf-Of-Django-Groups`` header
2. Django database backend using Fedora Repository for storing data and Elasticsearch for indexing/searching

.. _mapping-ids:

***********
ORM mapping
***********

Mapping IDs
===========

Django needs the ``id`` attribute to hold an integer value. On the other hand, in Fedora repository objects are
identified by their URLs. To keep the ``id`` mechanism functioning, there are two helper functions in
``fedoralink.idmapping`` module::

    def url2id(url):
        """
            Serialize url into a number
            that is compatible with django ids
        """
        return int.from_bytes(url.encode('utf-8'),
                              byteorder='big', signed=False)


    def id2url(django_id):
        """
            Return url out of django id created by url2id
        """
        num_bytes = django_id.bit_length() / 8 + 1
        return django_id.
            to_bytes(num_bytes,
                     byteorder='big', signed=False).decode('utf-8')


When an object is created/retrieved from Fedora, its ``url`` is transformed via ``url2id`` into a large integer.
During ``save``, it is transformed back via ``id2url``.

Note: these functions require at least python 3.2
