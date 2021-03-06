from rdflib.namespace import DC
from django.utils.translation import ugettext_lazy as _

from fedoralink.fedorans import CESNET
from fedoralink.indexer.fields import IndexedLanguageField, IndexedTextField, IndexedDateTimeField
from fedoralink.indexer.models import IndexableFedoraObject



#
# DCObject is indexable and provides .title and .creator property, that get mapped to
# DC.* predicates in RDF by simple_namespace_mapper
#
class DCObject(IndexableFedoraObject):

    title         = IndexedLanguageField(DC.title, required=True,
                                         verbose_name=_('Title'))

    alternative   = IndexedTextField(DC.alternative,
                                     verbose_name=_('Alternative title'))

    abstract      = IndexedLanguageField(DC.abstract,
                                         verbose_name=_('Abstract'),
                                         attrs={'presentation': 'textarea'})

    creator       = IndexedTextField(DC.creator,
                                     verbose_name=_('Creator'))

    contributor   = IndexedTextField(DC.contributor,
                                     verbose_name=_('Contributor'))

    dateSubmitted = IndexedDateTimeField(DC.dateSubmitted,
                                         verbose_name=_('Date submitted'))

    dateAvailable = IndexedDateTimeField(DC.dateAvailable,
                                         verbose_name=_('Date available'))

    class Meta:
        rdf_types = (DC.Object,)

class DCObjectCollection(DCObject):

    class Meta:
        rdf_types = (CESNET.DCTermsCollection, )
