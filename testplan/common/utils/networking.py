"""
Utility functions related to networking
"""

import socket
import ipaddress


def port_to_int(port):
    """Convert a port string to an integer."""
    try:
        return int(port)
    except ValueError:
        return socket.getservbyname(port)


def get_hostname_access_url(port, url_path):
    return f"http://{socket.getfqdn()}:{port}{url_path}"
