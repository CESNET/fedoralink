from django.db.models import Model, TextField, CharField
from rdflib.namespace import DC, DCTERMS
from django.utils.translation import ugettext_lazy as _

from fedoralink.fields import FedoraField
from fedoralink.models import fedora


#
# DCObject is indexable and provides .title and .creator property, that get mapped to
# DC.* predicates in RDF by simple_namespace_mapper
#
@fedora(namespace=DC, primary_rdf_type=DC.object)
class DCObject(Model):

    _dcmitypes = ('Collection', 'Dataset', 'Event', 'Image', 'InteractiveResource',
                 'Service', 'Software', 'Sound', 'Text', 'PhysicalObject')
    _dcmitypes = [(x, x) for x in _dcmitypes]

    # Fields according to http://dublincore.org/documents/2012/06/14/dcmi-terms/ specification
    #
    # Fields in the /elements/1.1/ namespace
    title = TextField(verbose_name=_('Title'), default='')
    creator = TextField(verbose_name=_('Creator'), default='')
    subject = FedoraField(CharField(verbose_name=_('Subject'), default='', max_length=255),
                          multiplicity=FedoraField.ANY, rdf_namespace=DC, rdf_name=DC.subject)
    description = TextField(verbose_name=_('Description'), default='')
    publisher = CharField(verbose_name=_('Publisher'), default='', max_length=255)
    contributor = FedoraField(CharField(verbose_name=_('Contributor'), default='', max_length=255),
                              multiplicity=FedoraField.ANY, rdf_namespace=DC, rdf_name=DC.contributor)
    date = CharField(verbose_name=_('Date'), default='', max_length=128)
    type = CharField(verbose_name=_('Type'), choices=_dcmitypes, default='Text', max_length=20)
    dformat = TextField(verbose_name=_('Format'), default='')
    identifier = CharField(verbose_name=_('Identifier'), max_length=255, default='')
    source = CharField(verbose_name=_('Source'), max_length=255)
    language = FedoraField(CharField(verbose_name=_('Language'), max_length=128),
                           multiplicity=FedoraField.ANY, rdf_namespace=DC, rdf_name=DC.language)
    relation = TextField(verbose_name=_('Relation'), default='')
    coverage = CharField(verbose_name=_('Coverage'), default='', max_length=255)
    rights = FedoraField(TextField(verbose_name=_('Rights'), default=''),
                         multiplicity=FedoraField.ANY, rdf_namespace=DC, rdf_name=DC.rights)

    # Fields in the /terms/ namespace
    abstract = FedoraField(TextField(verbose_name=_('Abstract'), default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.abstract)
    accessRights = FedoraField(CharField(max_length=255, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.accessRights)
    accrualMethod = FedoraField(CharField(max_length=255, default=''),
                                rdf_namespace=DCTERMS, rdf_name=DCTERMS.accrualMethod)
    accrualPeriodicity = FedoraField(CharField(max_length=128, default=''),
                                     rdf_namespace = DCTERMS, rdf_name = DCTERMS.accrualPeriodicity)
    accrualPolicy = FedoraField(CharField(max_length=255, default=''),
                                rdf_namespace=DCTERMS, rdf_name=DCTERMS.accrualPolicy)
    alternative = FedoraField(TextField(verbose_name=_('Alternative'), default=''),
                              rdf_namespace=DCTERMS, rdf_name=DCTERMS.alternative)
    audience = FedoraField(CharField(verbose_name=_('Audience'), max_length=255, default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.audience)
    available = FedoraField(CharField(verbose_name=_('Available'), max_length=128, default=''),
                            rdf_namespace=DCTERMS, rdf_name=DCTERMS.available)
    bibliographicCitation = FedoraField(TextField(verbose_name=_('Bibliography'), default=''),
                                        rdf_namespace=DCTERMS, rdf_name=DCTERMS.bibliographicCitation)
    conformsTo = FedoraField(CharField(max_length=255, default=''),
                             rdf_namespace=DCTERMS, rdf_name=DCTERMS.conformsTo)
    contributor_term = FedoraField(CharField(verbose_name=_('Contributor'), default='', max_length=255),
                                   rdf_namespace=DCTERMS, rdf_name=DCTERMS.contributor)
    coverage_term = FedoraField(CharField(verbose_name=_('Coverage'), default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.coverage)  #Recommended best practice is to use a controlled vocabulary such as the Thesaurus of Geographic Names [TGN]
    created = FedoraField(CharField(verbose_name=_('Created'), max_length=128, default=''),
                          rdf_namespace=DCTERMS, rdf_name=DCTERMS.created)
    creator_term = FedoraField(TextField(verbose_name=_('Creator'), default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.creator)
    date_term = FedoraField(CharField(verbose_name=_('Date'), max_length=128, default=''),
                            rdf_namespace=DCTERMS, rdf_name=DCTERMS.date)
    dateAccepted = FedoraField(CharField(verbose_name=_('Accepted'), max_length=128, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.dateAccepted)
    dateCopyrighted = FedoraField(CharField(verbose_name=_('Copyrighted'), max_length=128, default=''),
                                  rdf_namespace=DCTERMS, rdf_name=DCTERMS.dateCopyrighted)
    dateSubmitted = FedoraField(CharField(verbose_name=_('Submitted'), max_length=128, default=''),
                                rdf_namespace=DCTERMS, rdf_name=DCTERMS.dateSubmitted)
    description_term = FedoraField(TextField(verbose_name=_('Description'), default=''),
                                   rdf_namespace=DCTERMS, rdf_name=DCTERMS.description)
    educationLevel = FedoraField(CharField(verbose_name=_('Submitted'), max_length=225, default=''),
                                 rdf_namespace=DCTERMS, rdf_name=DCTERMS.educationLevel)
    extent = FedoraField(CharField(verbose_name=_('Extent'), max_length=225, default=''),
                         rdf_namespace=DCTERMS, rdf_name=DCTERMS.extent)
    dformat_term = FedoraField(CharField(verbose_name=_('Format'), max_length=225, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.format)  # Recommended best practice is to use a controlled vocabulary such as the list of Internet Media Types [MIME]. TODO: Already in elements ns, distinguish by ns
    hasFormat = FedoraField(CharField(max_length=225, default=''),
                            rdf_namespace=DCTERMS, rdf_name=DCTERMS.hasFormat)
    hasPart = FedoraField(CharField(max_length=225, default=''),
                          rdf_namespace=DCTERMS, rdf_name=DCTERMS.hasPart)
    hasVersion = FedoraField(CharField(max_length=225, default=''),
                             rdf_namespace=DCTERMS, rdf_name=DCTERMS.hasVersion)
    identifier_term = FedoraField(CharField(verbose_name=_('Identifier'), max_length=225, default=''),
                                  rdf_namespace = DCTERMS, rdf_name = DCTERMS.identifier)
    instructionalMethod = FedoraField(TextField(default=''),
                                      rdf_namespace=DCTERMS, rdf_name=DCTERMS.instructionalMethod)
    isFormatOf = FedoraField(CharField(max_length=225, default=''),
                             rdf_namespace=DCTERMS, rdf_name=DCTERMS.isFormatOf)
    isPartOf = FedoraField(CharField(max_length=225, default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.isPartOf)
    isReferencedBy = FedoraField(CharField(max_length=225, default=''),
                                 rdf_namespace=DCTERMS, rdf_name=DCTERMS.isReferencedBy)
    isReplacedBy = FedoraField(CharField(max_length=225, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.isReplacedBy)
    isRequiredBy = FedoraField(CharField(max_length=225, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.isRequiredBy)
    issued = FedoraField(CharField(verbose_name=_('Issued'), max_length=128, default=''),
                         rdf_namespace=DCTERMS, rdf_name=DCTERMS.issued)
    isVersionOf = FedoraField(CharField(max_length=225, default=''),
                              rdf_namespace=DCTERMS, rdf_name=DCTERMS.isVersionOf)
    language_term = FedoraField(CharField(verbose_name=_('Language'), max_length=128),
                                rdf_namespace=DCTERMS, rdf_name=DCTERMS.language)  # Recommended best practice is to use a controlled vocabulary such as RFC 4646 [RFC4646].
    license = FedoraField(TextField(verbose_name=_('License'), default=''),
                          rdf_namespace=DCTERMS, rdf_name=DCTERMS.license)
    mediator = FedoraField(CharField(verbose_name=_('Mediator'), max_length=255, default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.mediator)
    medium = FedoraField(CharField(verbose_name=_('Medium'), max_length=255, default=''),
                         rdf_namespace=DCTERMS, rdf_name=DCTERMS.medium)
    modified = FedoraField(CharField(verbose_name=_('Issued'), max_length=128, default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.modified)
    provenance = FedoraField(TextField(verbose_name=_('Provenance'), default=''),
                             rdf_namespace=DCTERMS, rdf_name=DCTERMS.provenance)
    publisher_term = FedoraField(CharField(verbose_name=_('Publisher'), max_length=255, default=''),
                                 rdf_namespace=DCTERMS, rdf_name=DCTERMS.publisher)
    references = FedoraField(CharField(verbose_name=_('References'), max_length=255, default=''),
                             rdf_namespace=DCTERMS, rdf_name=DCTERMS.references)
    relation_term = FedoraField(TextField(verbose_name=_('Relation'), default=''),
                                rdf_namespace=DCTERMS, rdf_name=DCTERMS.relation)
    replaces = FedoraField(CharField(max_length=225, default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.replaces)
    requires = FedoraField(CharField(max_length=225, default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.requires)
    rights_term = FedoraField(TextField(verbose_name=_('Rights'), default=''),
                              rdf_namespace=DCTERMS, rdf_name=DCTERMS.rights)
    rightsHolder = FedoraField(CharField(max_length=225, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.rightsHolder)
    source_term = FedoraField(CharField(verbose_name=_('Source'), max_length=255, default=''),
                              rdf_namespace=DCTERMS, rdf_name=DCTERMS.source)  #Recommended best practice is to identify the related resource by means of a string conforming to a formal identification system.
    spatial = FedoraField(TextField(verbose_name=_('Spatial'), default=''),
                          rdf_namespace=DCTERMS, rdf_name=DCTERMS.spatial)
    subject_term = FedoraField(CharField(verbose_name=_('Subject'), max_length=255, default=''),
                               rdf_namespace=DCTERMS, rdf_name=DCTERMS.subject)  #Recommended best practice is to use a controlled vocabulary.
    tableOfContents = FedoraField(TextField(verbose_name=_('TableOfContents'), default=''),
                                  rdf_namespace=DCTERMS, rdf_name=DCTERMS.tableOfContents)
    temporal = FedoraField(TextField(verbose_name=_('Temporal'), default=''),
                           rdf_namespace=DCTERMS, rdf_name=DCTERMS.temporal)
    title_term = FedoraField(TextField(verbose_name=_('Title'), default=''),
                             rdf_namespace=DCTERMS, rdf_name=DCTERMS.title)
    type_term = FedoraField(CharField(verbose_name=_('Type'), max_length=128),
                            rdf_namespace=DCTERMS, rdf_name=DCTERMS.type)  # Recommended best practice is to use a controlled vocabulary such as the DCMI Type Vocabulary [DCMITYPE]
    valid = FedoraField(CharField(verbose_name=_('Valid'), max_length=128, default=''),
                        rdf_namespace=DCTERMS, rdf_name=DCTERMS.valid)