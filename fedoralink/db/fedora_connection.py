import logging
import time
from urllib.parse import urljoin

import requests
from rdflib import Literal, XSD
from requests import HTTPError, RequestException
from requests.auth import HTTPBasicAuth

from fedoralink.authentication.as_user import fedora_auth_local
from fedoralink.db.rdf import RDFMetadata
# noinspection PyUnresolvedReferences
# import delegated_requests to wrap around
from .delegated_requests import get, post, put, delete

log = logging.getLogger(__file__)


class FedoraMixin(object):
    def __init__(self, *args, **kwargs):
        self.repo_url = kwargs['fcrepo_url']
        self.username = kwargs['fcrepo_username']
        self.password = kwargs['fcrepo_password']
        self.namespace_config = kwargs['namespace_config']

        if self.namespace_config.prefix:
            self.repo_url += '/%s' % self.namespace_config.prefix

    def create_resources(self, insert_query):
        """
        Creates a resource inside Fedora and returns its id (url)
        
        :param insert_query:        resource in Fedora 
        :return:                    url if the created resource
        """
        ids = []
        for object in insert_query.objects:
            rdf_metadata = RDFMetadata('')
            for fld, val in object['fields'].items():
                if not isinstance(val, Literal):
                    if isinstance(val, str):
                        val = Literal(val, datatype=XSD.string)
                    else:
                        val = Literal(val)
                rdf_metadata.add(fld[0], val)
            parent_url = object['parent']
            if not parent_url:
                parent_url = self.namespace_config.default_parent_for_inserted_object(object)
            parent_url = self._get_request_url(parent_url)
            created_id = self._create_object_from_metadata(parent_url, rdf_metadata, None)
            ids.append(created_id)

        raise NotImplementedError()

    def _create_object_from_metadata(self, parent_url, metadata, slug):
        payload = str(metadata)
        log.info('Creating child in %s', parent_url)
        log.debug("    payload %s", payload)
        try:
            headers = {'Content-Type': 'text/turtle; encoding=utf-8'}
            if slug:
                headers['SLUG'] = slug
            resp = post(parent_url, payload.encode('utf-8'), headers=headers, auth=self._get_auth())
            if resp.status_code >= 400:
                raise requests.HTTPError("Resource not created, error code %s : %s" % (resp.status_code, resp.content))
            created_object_id = resp.text

            # make a version
            self.make_version(created_object_id, time.time())

            return created_object_id

        except RequestException as e:
            log.exception("Error in creating object")
            raise

    def _get_auth(self):
        if (hasattr(fedora_auth_local, 'Credentials')):
            credentials = getattr(fedora_auth_local, 'Credentials')
            if credentials is not None:
                return HTTPBasicAuth(credentials.username, credentials.password)
        if self.username:
            return HTTPBasicAuth(self.username, self.password)
        else:
            return None

    def make_version(self, object_id, version):
        """
        Marks the current object data inside repository with a new version

        :param object_id:        id of the object. Might be full url or a fragment
                                 which will be appended after repository_url
        :param version:          the id of the version, [a-zA-Z_][a-zA-Z0-9_]*
        """
        requests.post(self._get_request_url(object_id) + '/fcr:versions',
                      headers={'Slug': 'snapshot_at_%s' % version}, auth=self._get_auth())

    def _get_request_url(self, object_id):
        if ':' in object_id and not object_id.startswith('http'):
            req_url = self.repo_url + '/' + object_id
        else:
            req_url = urljoin(self.repo_url, object_id)

        # if self._in_transaction:
        #     if not req_url.startswith(self._fedora_url):
        #         raise Exception('Could not make request url relative so that it can play part in transaction. ' +
        #                         'Object url %s, fedora url %s' % (req_url, self._fedora_url))
        #     req_url = req_url[len(self._fedora_url):]
        #     if req_url.startswith('/'):
        #         req_url = req_url[1:]
        #     if req_url.startswith('tx:'):
        #         slash_position = req_url.find('/')
        #         # TODO: check txid
        #         # txid = req_url[:slash_position]
        #         req_url = req_url[slash_position + 1:]
        #     req_url = self.dumb_concatenate_url(self._transaction_url, req_url)
        return req_url
