from django.db.models import Model, TextField, CharField
from rdflib.namespace import DC
from django.utils.translation import ugettext_lazy as _
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
    subject = CharField(verbose_name=_('Subject'), default='', max_length=255)
    description = TextField(verbose_name=_('Description'), default='')
    publisher = CharField(verbose_name=_('Publisher'), default='', max_length=255)
    contributor = CharField(verbose_name=_('Contributor'), default='', max_length=255)
    date = CharField(verbose_name=_('Date'), default='', max_length=128)
    type = CharField(verbose_name=_('Type'), choices=_dcmitypes, default='Text', max_length=20)
    dformat = TextField(verbose_name=_('Format'), default='')
    identifier = CharField(verbose_name=_('Identifier'), max_length=255, default='')
    source = CharField(verbose_name=_('Source'), max_length=255)
    language = CharField(verbose_name=_('Language'), max_length=128)
    relation = TextField(verbose_name=_('Relation'), default='')
    coverage = CharField(verbose_name=_('Coverage'), default='', max_length=255)
    rights = TextField(verbose_name=_('Rights'), default='')

    # Fields in the /terms/ namespace
    abstract = TextField(verbose_name=_('Abstract'), default='')
    accessRights = CharField(max_length=255, default='')
    accrualMethod = CharField(max_length=255, default='')
    accrualPeriodicity = CharField(max_length=128, default='')
    accrualPolicy = CharField(max_length=255, default='')
    alternative = TextField(verbose_name=_('Alternative'), default='')
    audience = CharField(verbose_name=_('Audience'), max_length=255, default='')
    available = CharField(verbose_name=_('Available'), max_length=128, default='')
    bibliographicCitation = TextField(verbose_name=_('Bibliography'), default='')
    conformsTo = CharField(max_length=255, default='')
    #contributor = CharField(verbose_name=_('Contributor'), default='') # TODO: Already in elements ns, distinguish by ns
    #coverage = CharField(verbose_name=_('Coverage'), default='') #Recommended best practice is to use a controlled vocabulary such as the Thesaurus of Geographic Names [TGN], TODO: Already in elements ns, distinguish by ns
    created = CharField(verbose_name=_('Created'), max_length=128, default='')
    #creator = TextField(verbose_name=_('Creator'), default='') # TODO: Already in elements ns, distinguish by ns
    #date = CharField(verbose_name=_('Date'), max_length=128, default='') # TODO: Already in elements ns, distinguish by ns
    dateAccepted = CharField(verbose_name=_('Accepted'), max_length=128, default='')
    dateCopyrighted = CharField(verbose_name=_('Copyrighted'), max_length=128, default='')
    dateSubmitted = CharField(verbose_name=_('Submitted'), max_length=128, default='')
    #description = TextField(verbose_name=_('Description'), default='') # TODO: Already in elements ns, distinguish by ns
    educationLevel = CharField(verbose_name=_('Submitted'), max_length=225, default='')
    extent = CharField(verbose_name=_('Extent'), max_length=225, default='')
    dformat = CharField(verbose_name=_('Format'), max_length=225, default='') # Recommended best practice is to use a controlled vocabulary such as the list of Internet Media Types [MIME]. TODO: Already in elements ns, distinguish by ns
    hasFormat = CharField(max_length=225, default='')
    hasPart = CharField(max_length=225, default='')
    hasVersion = CharField(max_length=225, default='')
    #identifier = CharField(verbose_name=_('Identifier'), max_length=225, default='') # TODO: Already in elements ns, distinguish by ns
    instructionalMethod = TextField(default='')
    isFormatOf = CharField(max_length=225, default='')
    isPartOf = CharField(max_length=225, default='')
    isReferencedBy = CharField(max_length=225, default='')
    isReplacedBy = CharField(max_length=225, default='')
    isRequiredBy = CharField(max_length=225, default='')
    issued = CharField(verbose_name=_('Issued'), max_length=128, default='')
    isVersionOf = CharField(max_length=225, default='')
    #language = CharField(verbose_name=_('Language'), max_length=128) # Recommended best practice is to use a controlled vocabulary such as RFC 4646 [RFC4646]. TODO: Already in elements ns, distinguish by ns
    license = TextField(verbose_name=_('License'), default='')
    mediator = CharField(verbose_name=_('Mediator'), max_length=255, default='')
    medium = CharField(verbose_name=_('Medium'), max_length=255, default='')
    modified = CharField(verbose_name=_('Issued'), max_length=128, default='')
    provenance = TextField(verbose_name=_('Provenance'), default='')
    #publisher = CharField(verbose_name=_('Publisher'), max_length=255, default='') # TODO: Already in elements ns, distinguish by ns
    references = CharField(verbose_name=_('References'), max_length=255, default='')
    #relation = TextField(verbose_name=_('Relation'), default='') # TODO: Already in elements ns, distinguish by ns
    replaces = CharField(max_length=225, default='')
    requires = CharField(max_length=225, default='')
    #rights = TextField(verbose_name=_('Rights'), default='') # TODO: Already in elements ns, distinguish by ns
    rightsHolder = CharField(max_length=225, default='')
    #source = CharField(verbose_name=_('Source'), max_length=255, default='') #Recommended best practice is to identify the related resource by means of a string conforming to a formal identification system. TODO: Already in elements ns, distinguish by ns
    spatial = TextField(verbose_name=_('Spatial'), default='')
    #subject = CharField(verbose_name=_('Subject'), max_length=255, default='') #Recommended best practice is to use a controlled vocabulary. TODO: Already in elements ns, distinguish by ns
    tableOfContents = TextField(verbose_name=_('TableOfContents'), default='')
    temporal = TextField(verbose_name=_('Temporal'), default='')
    #title = TextField(verbose_name=_('Title'), default='') # TODO: Already in elements ns, distinguish by ns
    #type = CharField(verbose_name=_('Type'), max_length=128) # Recommended best practice is to use a controlled vocabulary such as the DCMI Type Vocabulary [DCMITYPE] TODO: Already in elements ns, distinguish by ns
    valid = CharField(verbose_name=_('Valid'), max_length=128, default='')