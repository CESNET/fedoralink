from django.utils.translation import ugettext_lazy as _

# Create your models here.
from fedoralink.common_namespaces.dc import DCObject
from fedoralink.fedorans import CESNET_TYPE, CESNET, RDFS
from fedoralink.indexer.fields import IndexedTextField, IndexedField, IndexedLinkedField, IndexedIntegerField, \
    IndexedBooleanField
from fedoralink.indexer.models import IndexableFedoraObject


class AdministrationCollection(IndexableFedoraObject):
    class Meta:
        rdf_types = (CESNET_TYPE.AdministrationCollection,)


class ResourceTypeCollection(IndexableFedoraObject):
    class Meta:
        rdf_types = (CESNET_TYPE.ResourceTypeCollection,)


class Template(IndexableFedoraObject):
    label = IndexedTextField(CESNET_TYPE.label, verbose_name=_('Label'), level=IndexedField.MANDATORY)

    tags = IndexedTextField(CESNET_TYPE.tag, verbose_name=_('Tags'), multi_valued=True)

    class Meta:
        rdf_types = (CESNET_TYPE.Template,)


class Application(IndexableFedoraObject):

    label = IndexedTextField(CESNET_TYPE.label, verbose_name=_('Label'), level=IndexedField.MANDATORY)


class ResourceFieldType(IndexableFedoraObject):
    """
    A fedora model representing how a single field should get rendered (in view and in edit).
    Resolution order (first hit wins):

      1. same resource_type, field_name, field_fedoralink_type
      2. same resource_type, field_name
      3. same resource_type, field_fedoralink_type
      4. same field_name, field_fedoralink_type
      5. same field_name
      6. same field_fedoralink_type
    """
    label = IndexedTextField(CESNET_TYPE.label, verbose_name=_('Label'), level=IndexedField.MANDATORY)

    name = IndexedTextField(CESNET_TYPE.field_name, verbose_name=_('Field name'))

    field_type = IndexedTextField(RDFS.range,
                                  verbose_name=_('Field type as uri, either xsd:... or '
                                                 'a reference to ResourceType in case of linked fields'))

    cardinality = IndexedIntegerField(CESNET_TYPE.cardinality,
                                      verbose_name=_('Field Cardinality'),
                                      help_text=_('if empty any number of values allowed'))

    required    = IndexedBooleanField(CESNET.required, verbose_name=_('Required'))

    class Meta:
        rdf_types = (CESNET_TYPE.ResourceFieldType,)


class ResourceType(IndexableFedoraObject):

    label = IndexedTextField(CESNET_TYPE.label, verbose_name=_('Label'), level=IndexedField.MANDATORY)

    rdf_types = IndexedTextField(CESNET_TYPE.rdf_types, verbose_name=_('RDF types'), level=IndexedField.MANDATORY,
                                 multi_valued=True)

    fedoralink_model = IndexedTextField(CESNET_TYPE.fedoralink_model, verbose_name=_('Fedoralink model class name'),
                                        level=IndexedField.MANDATORY)

    fields = IndexedLinkedField(CESNET_TYPE.fields, ResourceFieldType,
                                verbose_name=_('Contained fields'))

    class Meta:
        rdf_types = (CESNET_TYPE.ResourceType,)


class ApplicationResourceType(IndexableFedoraObject):

    resource_type = IndexedLinkedField(CESNET_TYPE.resource_type, ResourceType)

    application = IndexedLinkedField(CESNET_TYPE.application, Application)

    template_view = IndexedLinkedField(CESNET_TYPE.template_view, Template, verbose_name=_('Template for view'))

    template_edit = IndexedLinkedField(CESNET_TYPE.template_edit, Template, verbose_name=_('Template for edit'))

    template_list_item = IndexedLinkedField(CESNET_TYPE.template_list_item, Template,
                                            verbose_name=_('Template for item list view'))

    controller = IndexedTextField(CESNET_TYPE.controller, verbose_name=_('Controller class'),
                                  level=IndexedField.MANDATORY)

    class Meta:
        rdf_types = (CESNET_TYPE.ApplicationResourceType,)


class ApplicationResourceFieldType(IndexableFedoraObject):

    resource_field_type = IndexedLinkedField(CESNET_TYPE.resource_field_type, ResourceFieldType)

    application = IndexedLinkedField(CESNET_TYPE.application, Application)

    template_field_detail_view = IndexedLinkedField(CESNET_TYPE.template_field_detail_view, Template,
                                                    verbose_name=_('Template for field inside detail view'))

    template_field_edit_view = IndexedLinkedField(CESNET_TYPE.template_field_edit_view, Template,
                                                  verbose_name=_('Template for field inside edit view'))

    class Meta:
        rdf_types = (CESNET_TYPE.ApplicationResourceFieldType,)

#
#
# class ResourceCollectionType(ResourceType):
#
#     template_search = IndexedLinkedField(CESNET_TYPE.template_search, Template,
#                                          verbose_name=_('Templates for list/search view'), multi_valued=True)
#
#     primary_child_type = IndexedLinkedField(CESNET_TYPE.primary_child_type, ResourceType,
#                                             verbose_name=_('Primary collection\'s child type, '
#                                                            'used for example for search or resource creation'))
#
#     primary_subcollection_type = IndexedLinkedField(CESNET_TYPE.primary_subcollection_type, ResourceType,
#                                                     verbose_name=_('Primary subcollection type, '
#                                                                    'used for example for search or resource creation'))
#
#     class Meta:
#         rdf_types = (CESNET_TYPE.ResourceCollectionType,)
#

class DCTermsCollection(DCObject):
    class Meta:
        rdf_types = (CESNET.DCTermsCollection,)


class Controller:
    nieco = 'nieco'  # TODO: create Controller
