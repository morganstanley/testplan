"""Unit tests for the HTTPServer and HTTPClient drivers."""

import uuid

import requests
import pytest

from testplan.testing.multitest.driver.http import HTTPServer, HTTPResponse, HTTPClient


def create_server(name, host, port):
    server = HTTPServer(name=name,
                        host=host,
                        port=port)
    server.start()
    server._wait_started()
    return server


def create_client(name, host, port, timeout):
    client = HTTPClient(name=name,
                        host=host,
                        port=port,
                        timeout=timeout)
    client.start()
    client._wait_started()
    return client


class TestHTTP(object):

    def setup_method(self, method):
        self.server = create_server('http_server', 'localhost', 0)
        self.client = create_client(
            'http_client',
            self.server.host,
            self.server.port,
            10
        )

    def teardown_method(self, method):
        for device in [self.server, self.client]:
            device.stop()
            device._wait_stopped()

    @pytest.mark.parametrize(
        'method',
        ('get', 'post', 'put', 'delete', 'patch', 'options')
    )
    def test_server_method_request(self, method):
        text = str(uuid.uuid4())
        res = HTTPResponse(content=[text])
        self.server.queue_response(res)

        method_request = getattr(requests, method)
        url = 'http://{}:{}/'.format(self.server.host, self.server.port)
        r = method_request(url)
        assert requests.codes.ok == r.status_code
        assert 'text/plain' == r.headers['content-type']
        assert text == r.text.strip('\n')

    @pytest.mark.parametrize(
        'method',
        ('get', 'post', 'put', 'delete', 'patch', 'options')
    )
    def test_client_method_request(self, method):
        method_request = getattr(self.client, method)
        method_request('random/text')

        text = str(uuid.uuid4())
        res = HTTPResponse(content=[text])
        self.server.queue_response(res)

        r = self.client.receive()

        assert requests.codes.ok == r.status_code
        assert 'text/plain' == r.headers['content-type']
        assert text == r.text.strip('\n')

    def test_client_flush(self):
        self.client.get('random/text')
        self.client.flush()
        msg = self.client.receive()
        assert None == msg
