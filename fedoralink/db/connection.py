import logging

from fedoralink.db.elasticsearch_connection import ElasticsearchMixin

log = logging.getLogger(__file__)


class FedoraConnection(ElasticsearchMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_option(self, option_name, option_value):
        raise Exception('Setting options on FedoraConnection is not yet implemented')

    def disconnect(self):
        pass
