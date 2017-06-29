import io
import logging
import os.path
import time
from contextlib import closing
from urllib.parse import urljoin

import rdflib
import requests
from django.db import models
from django.db.models import IntegerField
from rdflib import Literal, XSD, URIRef
from requests import RequestException
from requests.auth import HTTPBasicAuth

from fedoralink.authentication.as_user import fedora_auth_local
from fedoralink.db.exceptions import RepositoryException
from fedoralink.db.lookups import get_column_ids, FedoraIdColumn, FedoraMetadataAnnotation
from fedoralink.db.queries import FedoraResourceScanner, FedoraMetadata
from fedoralink.db.rdf import RDFMetadata
from fedoralink.fields import FedoraField
from fedoralink.idmapping import url2id
# noinspection PyUnresolvedReferences
# import delegated_requests to wrap around
from .delegated_requests import post, delete
from urllib.parse import urljoin, quote


log = logging.getLogger(__file__)


class FedoraConnection(object):
    def __init__(self, *args, **kwargs):
        self.repo_url = kwargs['fcrepo_url']
        self.username = kwargs['fcrepo_username']
        self.password = kwargs['fcrepo_password']
        self.namespace_config = kwargs['namespace_config']

        if not self.repo_url.endswith('/'):
            self.repo_url += '/'

        if self.namespace_config.prefix:
            self.repo_url += '%s' % self.namespace_config.prefix
            if not self.repo_url.endswith('/'):
                self.repo_url += '/'

    def create_resources(self, insert_query):
        """
        Creates a resource inside Fedora and returns its id (url)
        
        :param insert_query:        resource in Fedora 
        :return:                    url if the created resource
        """
        ids = []
        for saved_object in insert_query.objects:
            rdf_metadata = self.get_object_rdf_metadata('', saved_object['fields'])
            parent_url = saved_object['parent']
            if not parent_url:
                parent_url = self.namespace_config.default_parent_for_inserted_object(saved_object)
            if parent_url is None:
                parent_url = ''
            parent_url = self._get_request_url(parent_url)
            created_id = self._create_object_from_metadata(parent_url, rdf_metadata, saved_object.get('slug', None))
            ids.append(created_id)
        return ids

    @staticmethod
    def get_object_rdf_metadata(pk, fields):
        rdf_metadata = RDFMetadata(pk)
        for fld, vals in fields.items():
            cvals = FedoraConnection._cast_to_rdf_value(vals)
            for val in cvals:
                rdf_metadata.add(fld[0], val)
        return rdf_metadata

    @staticmethod
    def _cast_to_rdf_value(vals):
        if not isinstance(vals, list) and not isinstance(vals, tuple):
            vals = [vals]
        cvals = []
        for val in vals:
            if not isinstance(val, Literal):
                if isinstance(val, str):
                    val = Literal(val, datatype=XSD.string)
                else:
                    val = Literal(val)
            cvals.append(val)
        return cvals

    def _create_object_from_metadata(self, parent_url, metadata, slug):
        payload = str(metadata)
        log.info('Creating child in %s', parent_url)
        # print('Creating child in %s, slug %s' % ( parent_url, slug))
        # import traceback
        # traceback.print_stack()
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

    def delete_all_data(self):
        if not self.namespace_config.prefix:
            raise NotImplementedError("Can not delete_all_data for non-prefixed data yet")

        delete(self.repo_url, auth=self._get_auth())
        tombstone_url = self.repo_url
        if not tombstone_url.endswith('/'):
            tombstone_url += '/'
        tombstone_url += 'fcr:tombstone'
        delete(tombstone_url, auth=self._get_auth())

    def get_object(self, object_id, fetch_child_metadata=False):
        """
        Fetches the resource with the given object_id parameter

        :param object_id: id of the object. Might be full url or a fragment which will be appended after repository_url
        :param fetch_child_metadata: if True, fetch also basic metadata about children. If False, do not fetch them,
                                     the only way to access children is via their url from .metadata[LDP.contains]
        :return:    the RDFMetadata of the fetched object
        """
        try:
            req_url = self._get_request_url(object_id)
            log.info('Requesting url %s' % req_url)
            headers = {
                'Accept' : 'application/rdf+xml; encoding=utf-8',
            }
            if fetch_child_metadata:
                headers['Prefer'] = 'return=representation; ' + \
                                    'include="http://fedora.info/definitions/v4/repository#EmbedResources"'

            with closing(requests.get(req_url + "/fcr:metadata",
                                      headers=headers, auth=self._get_auth())) as r:

                g = rdflib.Graph()
                log.debug("making request to %s", req_url)
                log.debug(r.headers)
                log.debug(r.raw)
                # for chunk in r.iter_content(chunk_size=1024):
                #     if chunk:
                #         print("chunk")
                #         print(chunk)
                #         r.content += chunk
                data = r.content.decode('utf-8')
                if r.status_code // 100 != 2:
                    raise RepositoryException(url=req_url, code=r.status_code,
                                              msg='Error accessing repository: %s' % data,
                                              hdrs=r.headers)

            log.debug("   ... data %s", data)
            g.parse(io.StringIO(data))
            yield RDFMetadata(req_url, g)

        except RequestException as e:
            log.exception("Error in getting object with url %s", object_id)
            raise

    def execute_search_by_pk(self, query):
        # get the object from fedora
        try:
            obj = next(self.get_object(query.pk))
            obj = self.convert_to_row(query.query.model, get_column_ids(query.compiler.select), obj)
            return FedoraResourceScanner([obj])
        except RepositoryException:
            return FedoraResourceScanner([])

    def convert_to_row(self, model, columns, obj):
        ret = []
        for rdf_name, search_name, field_name, fedora_col, django_field in columns:
            if django_field == model._meta.pk:
                ret.append(url2id(obj.id))
            elif isinstance(fedora_col, FedoraIdColumn):
                ret.append(obj.id)
            elif isinstance(fedora_col, FedoraMetadataAnnotation):
                ret.append(FedoraMetadata(obj, from_search=False))
            elif isinstance(django_field, models.CharField) or isinstance(django_field, models.TextField) or \
                    isinstance(django_field, IntegerField):
                field_data = obj[URIRef(field_name)]
                if len(field_data) == 0:
                    ret.append(None)
                elif len(field_data) > 1:
                    log.warning("Data of field %s can not be represented as a single string,\n"
                                "taking only the first item. Metadata:\n%s", rdf_name, obj)
                else:
                    ret.append(field_data[0].value)
            elif isinstance(django_field, FedoraField):
                # FedoraField.from_db_value will take care of converting Literal to target type
                ret.append(obj[URIRef(field_name)])
            else:
                raise NotImplementedError('Returning anything else than id is not implemented yet')
        return ret

    def update(self, query):
        metadata = self.get_object_rdf_metadata(query.pk, query.prev_data)
        # forget about "added" items
        metadata = RDFMetadata(query.pk, metadata.rdf_metadata)

        for fld, vals in query.update_data.items():
            cvals = FedoraConnection._cast_to_rdf_value(vals)
            metadata[fld[0]] = cvals
        self._update_single_resource(query.pk, metadata)

    def _update_single_resource(self, url, metadata, bitstream=None):
        payload = metadata.serialize_sparql()
        log.info("Updating object %s", url)
        log.debug("      payload %s", payload.decode('utf-8'))
        # print(payload.decode('utf-8'))
        try:
            if bitstream is not None:
                self._update_object_bitstream(url, bitstream)

            resp = requests.patch(url + "/fcr:metadata", data=payload,
                                  headers={'Content-Type': 'application/sparql-update; encoding=utf-8'},
                                  auth=self._get_auth())
            log.debug('Response: %s', resp.content)
            if resp.status_code // 100 != 2:
                raise Exception('Error updating resource in Fedora: %s' % resp.content)
            self.make_version(metadata.id, time.time())

            # need to get the metadata from the server as otherwise we would not be able to update the resource
            # later (Fedora mandates that last modification time in sent data is the same as last modification
            # time in the metadata on server)
            created_object_meta = list(self.get_object(metadata.id))[0]

            return created_object_meta

        except RequestException as e:
            log.error("Error updating resource", e)
            raise

    def _update_object_bitstream(self, url, bitstream):
        try:
            # TODO: this is because of Content-Length header, need to handle it more intelligently
            data = bitstream.stream.read()
            headers = {'Content-Type': bitstream.mimetype}
            if bitstream.filename:
                filename_header = 'filename="%s"' % quote(os.path.basename(bitstream.filename).encode('utf-8'))
                headers['Content-Disposition'] = 'attachment; ' + filename_header
            requests.put(url, data, headers=headers, auth=self._get_auth())

        except RequestException as e:
            log.error("Error updating bitstream", e)
            raise
