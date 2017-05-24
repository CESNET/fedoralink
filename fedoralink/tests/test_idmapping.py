import random
import string
from unittest import TestCase

from fedoralink.idmapping import url2id, id2url


class IdMappingTest(TestCase):
    """
    Test that idmapping between fedora and django ids work
    """
    def test_mapping(self):
        urls = [
            'http://localhost:8080/fcrepo/rest',
            'http://localhost:8080/fcrepo/rest/',
            'http://localhost:8080/fcrepo/rest/abc',
        ]

        for url in urls:
            self.check_url(url)

        for test_index in range(1000):
            suffix = ''.join(random.choice(string.ascii_uppercase + string.digits + '/') for _ in range(test_index + 1))
            self.check_url(urls[1] + suffix)

    def check_url(self, url):
        url_as_id = url2id(url)
        # each char takes one byte
        self.assertEqual(len(url), url_as_id.bit_length() // 8 + 1)

        self.assertEqual(type(url_as_id), int, 'Expected integer type of id')
        self.assertEqual(url, id2url(url_as_id), 'Id mapping failed')
