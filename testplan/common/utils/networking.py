"""
Utility functions related to networking
"""
from __future__ import (
    unicode_literals,
    print_function,
    division,
    absolute_import,
)
import socket
import ipaddress


def port_to_int(port):
    """Convert a port string to an integer."""
    try:
        return int(port)
    except ValueError:
        return socket.getservbyname(port)


def format_access_urls(host, port, url_path):
    """
    Format a string to log to give HTTP access to a URL endpoint listening
    on a particular host/port. Handles special 0.0.0.0 IP and formats IPV6
    addresses. The returned string is indented by 4 spaces.

    :param host: hostname or IP address
    :type host: ``str``
    :param port: port number
    :type port: ``int``
    :param url_path: path to format after host:port part of URL (expected to
        contain leading "/" e.g "/index.html")
    :type url_path: ``str``
    :return: a formatted string containing the connection URL(s)
    :rtype: ``str``
    """
    # Handle 0.0.0.0 as a special case: this means that the URL can be accessed
    # both via localhost or on any IP address this host owns.
    if host == "0.0.0.0":
        local_url = "http://localhost:{port}{path}".format(
            port=port, path=url_path
        )

        try:
            local_ip = socket.gethostbyname(socket.getfqdn())
            network_url = "http://{host}:{port}{path}".format(
                host=local_ip, port=port, path=url_path
            )

            return (
                "    Local: {local}\n"
                "    On Your Network: {network}".format(
                    local=local_url, network=network_url
                )
            )
        except socket.gaierror:
            return "    {}".format(local_url)
    else:
        # Check for an IPv6 address. Web browsers require IPv6 addresses
        # to be enclosed in [].
        try:
            if ipaddress.ip_address(host).version == 6:
                host = "[{}]".format(host)
        except ValueError:
            # Expected if the host is a host name instead of an IP address.
            pass

        url = "http://{host}:{port}{path}".format(
            host=host, port=port, path=url_path
        )
        return "    {}".format(url)
