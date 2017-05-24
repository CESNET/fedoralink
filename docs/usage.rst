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

 * ``id`` - the result of a mapping of Fedora object's URL into an integer. For details see :ref:`mapping-ids`.
 * ``fedora_id`` - the URL of a Fedora object, an instance of :py:obj:`rdflib.term.URIRef`.
 * ``fedora_meta`` - a dictionary-like object with URIRef keys and values represented
   as a list of :py:obj:`rdflib.term.Literal` or :py:obj:`rdflib.term.URIref` classes.
 * ``fedora_children`` - a manager returning child nodes of the current resource.
 * ``fedora_field_tracker`` - an instance of :py:obj:`model_utils.FieldTracker` that keeps the changes performed
   on model instance, so that only the changed properties get serialized to Fedora.


Retrieving objects by Fedora path
=================================

Use ``FedoraObject.objects.filter(fedora_id='...')`` or ``FedoraObject.objects.get(fedora_id='...')`` constructs
to access a Fedora repository object. You can also use
``FedoraObject.objects.filter(pk='...')`` or ``FedoraObject.objects.get(pk='...')`` though this is slightly less
efficient.

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

Test case:
    :file:`fedoralink.tests.test_by_pk`

Note:

    ``Q(pk=...)`` is not supported, only ``Q(fedora_id=...)`` can be used
    to query by object's uri within ``Q`` construct.

Retrieving objects by url from Elasticsearch instead of Fedora
--------------------------------------------------------------

The query above is quite slow because Fedora performs a lot of checks before the data are returned (for example,
WebAC). Sometimes it makes sense to fetch the data from Elasticsearch.

The manager on FedoraObject and on any model annotated with @fedora gives a ``.via(...)`` call that
can be currently called either with :data:`fedoralink.manager.REPOSITORY` (the default) or with
:data:`fedoralink.manager.ELASTICSEARCH`
to search within the Elasticsearch index.

Example::

   # get the root collection from elasticsearch,
   # without calling Elasticsearch first
   root = FedoraObject.objects.via(ELASTICSEARCH).get(pk='')


Note: Django's ``using`` and ``via`` are similar concepts: ``using`` selects a database on which an operation should
be performed, ``via`` switches the implementation of the search if applicable.

Test case:
    :file:`fedoralink.tests.test_pk_via_elasticsearch`


Querying objects by stored metadata
===================================

Even with untyped objects one can search by stored metadata. As the name of the metadatum is an RDF predicate
which is an URI, one can not use directly ``FedoraObject.objects.filter(http://...#organisation='CESNET')``.
Use the ``**`` operator to pass metadata names and values. The same holds also for ``Q`` constructs.

For example, the following filter can be used to filter all projects with 'CESNET' as an organization if there is a
``project`` ``doc_type`` within Elasticsearch's index::

  FedoraObject.objects.via('project').
      filter(**{URIRef('http://...#organization'): 'CESNET'})

Test case:
    :file:`fedoralink.tests.test_simple_store_fetch`



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


Test case:
    :file:`fedoralink.tests.test_migrate`