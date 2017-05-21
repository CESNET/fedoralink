from fedoralink.db.utils import rdf2search
from fedoralink.fedorans import CESNET, CESNET_TYPE


class FedoraFieldOptions:
    """
    Before an object is serialized to Fedora Repository, every field needs to have a mapping between
    django field name, rdf name in fedora and field name in Elasticsearch. This class adds the mapping.
    The :func:`fedoralink.models.fedora` decorator adds an instance of this mapping to each field of the
    decorated django model. See the decorator for details. 
    
    After decoration, an instance of this class is accessed via field.fedora_options, for example:
    
    :Example:
    
    >>>    Simple._meta.fields['name'].fedora_options
    
    
    :Attributes:
    
        * `field`:          django field to which these options were applied
        * `rdf_name`:       how is the field called inside Fedora Repository
        * `search_name`:    how is the field called inside Elasticsearch
    """

    def __init__(self, field=None, rdf_namespace=None, rdf_name=None):
        """
        Creates a new instance and populates search_name
        
        :param field:               django field instance
        :param rdf_name:            name of the field inside repository 
        :param rdf_namespace:       if rdf_name is not set, it is created from the rdf_namespace as
                                    rdf_namespace.<field.name>. rdf_namespace must be an instance of 
                                    :py:obj:`rdflib.namespace.Namespace` class.
        """
        self.field = field
        if rdf_name:
            self.rdf_name = rdf_name
        else:
            if not self.field:
                raise AttributeError('Please use rdf_name in FedoraFieldOptions constructor')
            self.rdf_name = getattr(rdf_namespace, self.field.name)

        self.search_name = rdf2search(self.rdf_name)


class FedoraOptions:
    """
    Before an object is serialized to Fedora Repository, there needs to be a mapping between
    the django object and its representation inside Fedora Repository and Elasticsearch. This class adds the mapping.
    The :func:`fedoralink.models.fedora` decorator adds an instance of this mapping to decorated django model. 
    See the decorator for details. 

    
    After decoration, an instance of this class is accessed via _meta.fedora_options, for example:
    
    :Example:
    
    >>>    Simple._meta.fedora_options

    
    :Attributes:
         * `clz`            the model class being decorated
         * `rdf_namespace`  the rdf namespace that is the default namespace for all fields
         * `rdf_types`      a list of rdf types a newly created object will receive
         * `field_options`  if passed it is a map of django_field_name => instance of FedoraFieldOptions. The instance
                        should not have the `field` attribute filled as it will be overwritten by this method
         * `explicitly_declared`  TODO: look into the router and document this
    """

    def __init__(self, clz, rdf_namespace=None, rdf_types=None, field_options=None, explicitly_declared=False):
        self.clz           = clz
        self.rdf_namespace = rdf_namespace
        self.explicitly_declared = explicitly_declared
        if not self.rdf_namespace:
            self.rdf_namespace = CESNET
        self.rdf_types     = rdf_types
        if not self.rdf_types:
            self.rdf_types = [getattr(CESNET_TYPE, self.clz._meta.db_table)]

        for parent in clz._meta.parents:
            if not hasattr(parent, '_meta'):
                continue
            if not hasattr(parent._meta, 'fedora_options'):
                FedoraOptions(parent, self.rdf_namespace)

        if not self.rdf_types:
            self.rdf_types = [
                getattr(self.rdf_namespace, clz._meta.db_table)
            ]

        for fld in clz._meta.fields:
            if not hasattr(fld, 'fedora_options'):
                if field_options and fld.name in field_options:
                    fld.fedora_options = field_options[fld.name]
                    fld.fedora_options.field = fld
                else:
                    fld.fedora_options = FedoraFieldOptions(field=fld, rdf_namespace=self.rdf_namespace)
