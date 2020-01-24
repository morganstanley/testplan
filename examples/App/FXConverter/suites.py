"""FX conversion tests."""

import os

from testplan.testing.multitest import testsuite, testcase


def msg_to_bytes(msg, standard='utf-8'):
    """Encode text to bytes."""
    return bytes(msg.encode(standard))


def bytes_to_msg(seq, standard='utf-8'):
    """Decode bytes to text."""
    return seq.decode(standard)


def custom_docstring_func(_, kwargs):
    """
    Return original docstring (if available) and
    parametrization arguments in the format ``key: value``.
    """
    kwargs_strings = [
        '{}: {}'.format(arg_name, arg_value)
        for arg_name, arg_value in kwargs.items()
        ]
    return os.linesep.join(kwargs_strings)


@testsuite
class ConversionTests(object):
    """Sample currency conversion operations."""

    def __init__(self):
        self._rates = {'EUR': {'GBP': '0.90000'},
                       'GBP': {'EUR': '1.10000'}}

    @testcase(parameters=(
          ('EUR:GBP:1000', '900'),
          ('GBP:EUR:1000', '1100'),
          ('EUR:GBP:1500', '1350'),
          ('GBP:EUR:1500', '1650')
        ),
        docstring_func=custom_docstring_func
    )
    def conversion_parameterized(self, env, result, request, expect):
        """
        Client sends a request to the currency converter app.
        The converter retrieves the conversion rate from the downstream
        and sends back the converted result to the client.
        """
        env.client.send(msg_to_bytes(request))

        # App requests rates from server
        received = bytes_to_msg(env.server.receive(size=7))
        result.equal(request[:7], received,
                     'Downstream receives rate query.')
        source, target = received.split(':')
        rate = self._rates[source][target]
        result.log('Downstream sends rate: {}'.format(rate))
        env.server.send(msg_to_bytes(rate))

        # Client receives response.
        result.equal(int(expect),
                     int(bytes_to_msg(env.client.receive(size=1024))),
                     'Client received converted value.')


@testsuite
class EdgeCases(object):
    """Suite containing edge case scenarios."""

    @testcase
    def same_currency(self, env, result):
        """
        Client requests conversion to the same currency.
        No downstream is involved as no rate is needed.
        """
        request = 'EUR:EUR:2000'
        expect = '2000'
        result.log('Client request: {}'.format(request))
        env.client.send(msg_to_bytes(request))

        # Client receives response.
        result.equal(int(expect),
                     int(bytes_to_msg(env.client.receive(size=1024))),
                     'Client received converted value.')

    @testcase
    def zero_amount(self, env, result):
        """
        Client requests conversion of 0 amount.
        No downstream is involved as no rate is needed.
        """
        request = 'EUR:GBP:0'
        expect = '0'
        result.log('Client request: {}'.format(request))
        env.client.send(msg_to_bytes(request))

        # Client receives response.
        result.equal(int(expect),
                     int(bytes_to_msg(env.client.receive(size=1024))),
                     'Client received converted value.')

    @testcase(parameters=(
          'GBP.EUR.1000', 'EUR::GBP:500', 'GBP:EURO:1000', 'GBP:EUR:ABC'
          ),
          docstring_func=custom_docstring_func
    )
    def invalid_requests(self, env, result, request):
        """
        Client sends a request with incorrect format.
        Requests are matched by [A-Z]{3}:[A-Z]{3}:[0-9]+ regex.
        """
        env.client.send(msg_to_bytes(request))

        # Client receives response.
        result.contain('Invalid request format',
                       bytes_to_msg(env.client.receive(size=1024)),
                       'Invalid request error received.')


@testsuite
class RestartEvent(object):
    """Converter app restart and reconnect scenarios."""

    def _send_and_receive(self, env, result, request, rate, expect):
        """
        Client sends a request to the currency converter app.
        The converter retrieves the conversion rate from the downstream
        and sends back the converted result to the client.
        """
        result.log('Client sends request: {}'.format(request))
        env.client.send(msg_to_bytes(request))

        # App requests rates from server
        received = bytes_to_msg(env.server.receive(size=7))
        result.equal(request[:7], received,
                     'Downstream receives rate query.')
        result.log('Downstream sends rate: {}'.format(rate))
        env.server.send(msg_to_bytes(rate))

        # Client receives response.
        result.equal(int(expect),
                     int(bytes_to_msg(env.client.receive(size=1024))),
                     'Client received converted value.')

    def _restart_components(self, env, result):
        """
        Restart converter app.
        Accept new connection from rate sending server.
        Restart client driver to connect to new host:port.
        """
        result.log('Restarting converter app.')
        env.converter.restart()
        result.log('App is now listening on {}:{}'.format(
            env.converter.host, env.converter.port))
        env.server.accept_connection()
        env.client.restart()

    @testcase
    def restart_app(self, env, result):
        """
        Restarting converter app and reconnect with rate
        server and client components before doing new requests.
        """
        result.log('App is listening on {}:{}'.format(
            env.converter.host, env.converter.port))
        self._send_and_receive(
            env, result, 'EUR:GBP:1000', '0.8500', '850')
        self._restart_components(env, result)
        self._send_and_receive(
            env, result, 'EUR:GBP:1000', '0.8700', '870')
        self._restart_components(env, result)
        self._send_and_receive(
            env, result, 'EUR:GBP:2000', '0.8300', '1660')
