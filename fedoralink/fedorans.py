from rdflib import Namespace, URIRef
from os.path import abspath
from django.conf import settings
from django.core.cache import cache


NAMESPACES = cache.get('NAMESPACES')

if not NAMESPACES:
    NAMESPACES = {}
    with open(abspath(settings.FEDORA_NODE_TYPES), 'r') as fedoraNodeTypesConf:
        for line in fedoraNodeTypesConf:
            if line.startswith('<') and '=' in line:
                name, url = line.lstrip('<').replace('>','').replace("'", '').replace(' ', '').strip().split('=', 1)
                if 'http' not in url:
                    continue
                NAMESPACES[name] = url
    cache.set('NAMESPACES', NAMESPACES, 3600)

FEDORA          =   Namespace(NAMESPACES['fedora']) if 'fedora' in NAMESPACES else None
FEDORA_CREATED_METADATA = URIRef(FEDORA.created)
FEDORA_LAST_MODIFIED_BY_METADATA = URIRef(FEDORA.lastModifiedBy)
FEDORA_PRIMARY_TYPE_METADATA = URIRef(FEDORA.primaryType)
FEDORA_MIXIN_TYPES_METADATA = URIRef(FEDORA.mixinTypes)
FEDORA_LAST_MODIFIED_METADATA = URIRef(FEDORA.lastModified)

RDF             =   Namespace(NAMESPACES['rdf']) if 'rdf' in NAMESPACES else None
RDFS            =   Namespace(NAMESPACES['rdfs']) if 'rdfs' in NAMESPACES else None
LDP             =   Namespace(NAMESPACES['ldp']) if 'ldp' in NAMESPACES else None

EBUCORE         =   Namespace(NAMESPACES['ebucore']) if 'ebucore' in NAMESPACES else None
PREMIS          =   Namespace(NAMESPACES['premis']) if 'premis' in NAMESPACES else None

CESNET          =   Namespace(NAMESPACES['cesnet']) if 'cesnet' in NAMESPACES else None
CESNET_STATE    =   Namespace(NAMESPACES['cesnet_state']) if 'cesnet_state' in NAMESPACES else None
CESNET_TYPE     =   Namespace(NAMESPACES['cesnet_type']) if 'cesnet_type' in NAMESPACES else None
ACL             =   Namespace(NAMESPACES['acl']) if 'acl' in NAMESPACES else None




