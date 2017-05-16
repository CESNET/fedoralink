Usage
=====

Untyped access
--------------

Typed access via models
-----------------------

Django ORM can be used to access Fedora repository in a "django" way, via defining custom models,
performing migrations and using the models.

Writing fedora database models
------------------------------

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