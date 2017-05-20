import re

from fedoralink.fedorans import NAMESPACES


def rdf2search(rdf_name):
    tmp_search_name = str(rdf_name)
    search_name = []
    for rev in re.findall('(([a-zA-Z0-9]+)|([^a-zA-Z0-9]))', tmp_search_name):
        if rev[1]:
            search_name.append(rev[1])
        else:
            search_name.append('_%x_' % ord(rev[2][0]))

    return ''.join(search_name)
