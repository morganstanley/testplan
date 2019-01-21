"""Example test script for use by PyTest."""
# For the most basic usage, no imports are required.
# pytest will automatically detect any test cases based
# on methods starting with ``test_``.

import pytest


class TestClassOne(object):
    # Trivial test method that will simply cause the test to succeed.
    # Note the use of the plain Python assert statement.
    def test_success(self):
        assert True

    # Similar to above, except this time the test case will always fail.
    def test_failure(self):
        assert False

    # Parametrized testcases
    @pytest.mark.parametrize("a,b,c", [
        (1, 2, 3),
        (-1, -2, -3),
        (0, 0, 0)
    ])
    def test_parametrization(self, a, b, c):
        assert a + b == c


class TestClassTwo(object):
    # Similarly MultiTest drivers are also available for PyTest.
    # The testcase can access those drivers by parameter `env`,
    # and make assertions provided by `result`.
    def test_drivers(self, env, result):
        message = 'This is a test message'
        env.server.accept_connection()
        size = env.client.send(bytes(message.encode('utf-8')))
        received = env.server.receive(size)
        result.log('Received Message from server: {}'.format(received),
                   description='Log a message')
        result.equal(received.decode('utf-8'), message,
                     description='Expect a message')
