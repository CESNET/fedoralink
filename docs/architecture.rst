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

Blah