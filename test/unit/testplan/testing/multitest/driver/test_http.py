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


def stop_devices(devices):
    for device in devices:
        device.stop()
        device._wait_stopped()


@pytest.mark.parametrize(
    'method',
    ('get', 'post', 'put', 'delete', 'patch', 'options')
)
def test_server_method_request(method):
    server = create_server('http_server', 'localhost', 0)

    text = str(uuid.uuid4())
    res = HTTPResponse(content=[text])
    server.queue_response(res)

    method_request = getattr(requests, method)
    r = method_request('http://{}:{}/'.format(server.host, server.port))

    assert requests.codes.ok == r.status_code
    assert 'text/plain' == r.headers['content-type']
    assert text == r.text.strip('\n')

    stop_devices([server])


@pytest.mark.parametrize(
    'method',
    ('get', 'post', 'put', 'delete', 'patch', 'options')
)
def test_client_method_request(method):
    server = create_server('http_server', 'localhost', 0)
    client = create_client('http_client', server.host, server.port, 10)

    method_request = getattr(client, method)
    method_request('random/text')

    text = str(uuid.uuid4())
    res = HTTPResponse(content=[text])
    server.queue_response(res)

    r = client.receive()

    assert requests.codes.ok == r.status_code
    assert 'text/plain' == r.headers['content-type']
    assert text == r.text.strip('\n')

    stop_devices([server, client])
