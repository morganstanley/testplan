"""Unit tests for the HTTPServer and HTTPClient drivers."""

import os
import time
import uuid

import requests
import pytest

from testplan.testing.multitest.driver import http
from testplan.common.utils import path


@pytest.fixture(scope="module")
def http_server(runpath_module):
    """Start and yield an HTTP server driver."""
    server = http.HTTPServer(
        name="http_server", host="localhost", port=0, runpath=runpath_module
    )

    with server:
        yield server


@pytest.fixture(scope="module")
def http_client(http_server, runpath_module):
    """Start and yield an HTTP client."""
    client = http.HTTPClient(
        name="http_client",
        host=http_server.host,
        port=http_server.port,
        timeout=10,
        runpath=runpath_module,
    )

    with client:
        yield client


class TestHTTP:
    """Test the HTTP server and client drivers."""

    @pytest.mark.parametrize(
        "method", ("get", "post", "put", "delete", "patch", "options")
    )
    def test_server_method_request(self, method, http_server):
        """Test making HTTP requests to the server directly using requests."""
        text = str(uuid.uuid4())
        res = http.HTTPResponse(content=[text])
        http_server.queue_response(res)

        method_request = getattr(requests, method)
        url = "http://{}:{}/".format(http_server.host, http_server.port)
        r = method_request(url)
        assert requests.codes.ok == r.status_code
        assert "text/plain" == r.headers["content-type"]
        assert text == r.text.strip("\n")

    def test_wait_for_response(self, http_server, http_client):
        """Test waiting for a response from the server."""
        # Send HTTP request
        http_client.get("random/text")

        # Send response
        wait = 0.2
        time.sleep(wait)
        text = str(uuid.uuid4())
        res = http.HTTPResponse(content=[text])
        http_server.respond(res)

        # Receive response
        r = http_client.receive()

        # Verify response
        assert requests.codes.ok == r.status_code
        assert "text/plain" == r.headers["Content-type"]
        assert text == r.text

    @pytest.mark.parametrize(
        "method", ("get", "post", "put", "delete", "patch", "options")
    )
    def test_client_method_request(self, method, http_server, http_client):
        """Test making HTTP requests from client to server objects."""
        method_request = getattr(http_client, method)
        method_request("random/text")

        text = str(uuid.uuid4())
        res = http.HTTPResponse(content=[text])
        http_server.queue_response(res)

        r = http_client.receive()

        assert requests.codes.ok == r.status_code
        assert "text/plain" == r.headers["content-type"]
        assert text == r.text.strip("\n")

    def test_server_flush(self, http_server):
        """Test flushing the server request queue."""
        http_server.flush_request_queue()
        msg = http_server.receive(timeout=0.5)
        assert msg is None

    @pytest.mark.parametrize("method", ("put", "post"))
    def test_client_method_request_with_data(
        self, method, http_server, http_client
    ):
        """Test making HTTP requests from client to server objects."""
        _URL = "/random/text"
        _CONTENT_TYPE_KEY = "Content-Type"
        _CONTENT_TYPE = "application/json"

        method_request = getattr(http_client, method)
        json_content = {"this": ["is", "a", "json", "object"]}
        method_request(
            api=_URL,
            json=json_content,
            headers={_CONTENT_TYPE_KEY: _CONTENT_TYPE},
        )

        r = http_server.receive(timeout=10)

        assert _CONTENT_TYPE == r.headers[_CONTENT_TYPE_KEY]
        assert json_content == r.json
        assert _URL == r.path_url

    def test_client_flush(self, http_client):
        """Test flushing the client receive queue."""
        http_client.get("random/text")
        http_client.flush()
        msg = http_client.receive(timeout=0.1)
        assert msg is None
