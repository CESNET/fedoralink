#####
Usage
#####

Fedoralink supports two usage modes: typed (i.e. Django-ORM) and untyped access to Fedora repository.

**************
Untyped access
**************

Using the untyped access scenario, user can retrieve/create/update/search for objects in Fedora repository
in an untyped way, circumventing Django ORM mapping. Use this approach for quick access to Fedora or in cases
where the model is too complex/variable to be meaningfully represented as django models.

Every object in Fedora can be accessed via FedoraObject class.
Instances of the object have the following properties:

 * ``id`` is the result of a mapping of Fedora object's URL into an integer. For details see :ref:`mapping-ids`.
 * ``fedora_id`` is the URL of a Fedora object.
 * ``fedora_meta`` is a dictionary-like object with string keys and values represented as a list of rdflib Literal classes.
 * ``fedora_children`` is a manager returning child nodes of the current resource.


Retrieving objects by Fedora path
=================================

Use ``FedoraObject.objects.filter(pk='...')`` or ``FedoraObject.objects.get(pk='...')`` constructs
to access a Fedora repository object.

Example::

    # get the root collection
    root = FedoraObject.objects.get(pk='')

    # print the id
    print("Resource url is %s, mapped to django integer id %s" %
              (root.fedora_id, root.id))

    # print the rdf:types of the root
    print("Resource RDF types:", root.fedora_meta[RDF.type])

    # get all child nodes inside the root collection
    print("Child nodes")
    for child in root.fedora_children.all():
        print("    ", child.fedora_id)


Retrieving the objects from Elasticsearch instead of Fedora
-----------------------------------------------------------

The query above is quite slow because Fedora performs a lot of checks before the data are returned (for example,
WebAC). Sometimes it makes sense to fetch the data from Elasticsearch.

The manager on FedoraObject and on any model annotated with @fedora gives a ``.via(...)`` call that
can be currently called either with ``REPOSITORY`` (the default) or with a ``doc_type`` within
the Elasticsearch index.

Example::

   # get the root collection from elasticsearch,
   # without calling Elasticsearch first
   root = FedoraObject.objects.via('dcobjects').get(pk='')

In this example we suppose that the root object is a dc:object and that there is a ``doc_type`` called ``dcobjects``
within Elasticsearch index.

Note: Django's ``using`` and ``via`` are similar concepts: ``using`` selects a database on which an operation should
be performed, ``via`` switches the implementation of the search if applicable.

Note: If you use typed approach (see :ref:`typed-access`), doc_type mapping is created automatically for you,
documents are automatically indexed and the ``via`` statement is added automatically on the model's manager.


Querying objects by stored metadata
===================================

Even in the untyped objects one can query objects by stored metadata. As the name of the metadatum is an RDF predicate
which is an URI, one can not use directly ``FedoraObject.objects.filter(http://...#organisation='CESNET')``.
Use the ``**`` operator to pass metadata names and values. The same holds also for ``Q`` constructs.

For example, the following filter can be used to filter all projects with 'CESNET' as an organization if there is a
``project`` ``doc_type`` within Elasticsearch's index::

  FedoraObject.objects.via('project').
      filter(**{'http://...#organization': 'CESNET'})


.. _typed-access:

***********************
Typed access via models
***********************

Django ORM can be used to access Fedora repository in a "django" way, via defining custom models,
performing migrations and using the models.

Writing fedora database models
==============================

Fedora database model looks completely same as any other Django model. In fact, with a database router,
any Django model can be stored inside Fedora Repository. The following model fields are currently supported:

 * ``AutoField``
 * ``CharField``
 * ``IntegerField``
 * ``FloatField``
 * ``DateTimeField``

Sample models.py::

    @fedora(namespace=CESNET)
    class Simple(models.Model):
        pass

The annotation is optional. If used:

 * the model is automatically routed to the *'repository'* database unless defined otherwise
 * defines the RDF namespace within which fields are created
 * defines the RDF types that are associated with the python class (see the mapping details)
 * to route to a different database, pass django's *'using'* definition in meta or manager methods

If the annotation is not used:
 * the model gets the CESNET rdf namespace and CESNET:modelname rdf:type
 * it is not routed to fedora repository. To make the routing, pass the database via
   *'using'* definition in meta or manager methods or a custom router

After the model is created, run::

    python manage.py makemigrations <myapp>
    python manage.py migrate --database repository <myapp>