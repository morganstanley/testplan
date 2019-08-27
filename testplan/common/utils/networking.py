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


def port_to_int(port):
    try:
        return int(port)
    except ValueError:
        return socket.getservbyname(port)
