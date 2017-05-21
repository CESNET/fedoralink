import re

from rdflib import URIRef


def rdf2search(rdf_name):
    tmp_search_name = str(rdf_name)
    search_name = []
    for rev in re.findall('(([a-zA-Z0-9]+)|([^a-zA-Z0-9]))', tmp_search_name):
        if rev[1]:
            search_name.append(rev[1])
        else:
            search_name.append('_%02x' % ord(rev[2][0]))

    return ''.join(search_name)


def search2rdf(search_name):
    ret = []
    print(search_name)
    for rev in re.findall('(([^_]+)|(_..))', search_name):
        if rev[1]:
            ret.append(rev[1])
        else:
            rev = rev[2][1:]
            ret.append(chr(int(rev, 16)))
    return URIRef(''.join(ret))
