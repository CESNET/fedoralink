from django.contrib.auth.models import User, Group
from django.db.models import ForeignKey, SET_NULL, CharField, Model
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices

from fedoralink.common_namespaces.dc.models import DCObject
from fedoralink.fedorans import ACL

from fedoralink.fields import FedoraField
from fedoralink.models import fedora, FedoraObject


@fedora(namespace=ACL, rdf_types=(ACL.Authorization,))
class Authorization(Model):
    ACL_PERMISSIONS = Choices(('http://www.w3.org/ns/auth/acl#Read', 'READ', 'Read'),
                              ('http://www.w3.org/ns/auth/acl#Write', 'WRITE', 'Write'))

    agent = FedoraField(CharField(null=True, max_length=512,
                                  verbose_name=_('People allowed to access a resource')),
                        multiplicity=FedoraField.ANY)

    agent_class = FedoraField(CharField(null=True, max_length=512,
                                        verbose_name=_('Groups of people allowed to access a resource')),
                              multiplicity=FedoraField.ANY)

    mode = FedoraField(CharField(max_length=512, choices=ACL_PERMISSIONS,
                                 verbose_name=_('Resource access mode, either acl:Read or acl:Write')),
                       multiplicity=FedoraField.ANY)

    access_to = FedoraField(ForeignKey(FedoraObject, on_delete=SET_NULL, null=True,
                                       verbose_name=_('Resource to which this object applies')),
                            multiplicity=FedoraField.ANY)

    access_to_class = FedoraField(CharField(max_length=512,
        verbose_name=_('RDF class of resources to which this authorization applies')), multiplicity=FedoraField.ANY)
