from fedoralink.common_namespaces.dc import DCObject
from fedoralink.fedorans import CESNET
from fedoralink.indexer.fields import IndexedIntegerField, IndexedTextField, IndexedLinkedField


class FedoraFieldType(DCObject):
    order        = IndexedIntegerField(CESNET.order)
    field_name   = IndexedTextField(CESNET.field_name)
    rdf_name     = IndexedTextField(CESNET.rdf_name)
    multi_valued = IndexedBooleanField(CESNET.multi_valued)
    required     = IndexedBooleanField(CESNET.required)
    field_type   = IndexedTextField(CESNET.field_type)

    class Meta:
        rdf_types = (CESNET.field,)


class FedoraType(DCObject):

    fields = IndexedLinkedField(CESNET.fields, FedoraFieldType, multi_valued=True)

    class Meta:
        rdf_types = (CESNET.type,)