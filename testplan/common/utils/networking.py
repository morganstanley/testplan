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
import random
from six.moves import range


def port_to_int(port):
    try:
        return int(port)
    except ValueError:
        return socket.getservbyname(port)


def unoccupied_ports(port_low_high, nb_ports):
    """
    Finds free TCP ports in the given range by binding to random ports in the range,
    until <nb_ports> free ports have been found.

    This does not guarantee that by the time caller tries to bind the ports will
    still be available.

    .. warning::

        You should *not* use this utility. Ever. That is because it is impossible to guarantee
        using anything outside the process that the port will be available by the time your application
        tries to bind to it : there is an inherent race condition happening here that we can't solve.
        The proper solution is to bind to port 0 and use ``getsockname(2)`` or its equivalent to make the port
        available to the caller, either through logs or other means, for instance
        :py:meth:`listening_addrs <ets.net.listening_addrs>`.

    :param port_low_high: port number for start  and end of range
    :type port_low_high: (``int``, ``int``)
    :param nb_ports: number of available ports required in given range
    :type nb_ports: ``int``

    :return: list of free ports numbers
    :rtype: ``list`` of ``int``
    """
    port_lo, port_hi = port_low_high
    if (port_hi - port_lo) < nb_ports:
        raise OSError(
            'Given range [{}, {}) is not big enough to find {} free ports'
            .format(port_lo, port_hi, nb_ports)
        )

    ports = list(range(port_lo, port_hi))
    avail_ports = []
    while ports and (len(avail_ports) < nb_ports):
        port = random.choice(ports)
        ports.remove(port)
        try:
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serversocket.bind(('0.0.0.0', port))
            serversocket.close()
            # Found free port
            avail_ports.append(port)
        except socket.error:
            pass

    if len(avail_ports) < nb_ports:
        raise OSError(
            'Could not find {} free ports in the range [{}, {}). Only found {}'
            .format(nb_ports, port_lo, port_hi, len(avail_ports))
        )
    return avail_ports


__ip_local_port_range_cache = None
def ip_local_port_range():
    """
    Return local ip port range on the machine

    :return: pair of integer port values
    :rtype: ``tuple`` of ``int``, ``int``
    """
    global __ip_local_port_range_cache
    if __ip_local_port_range_cache is None:
        with open('/proc/sys/net/ipv4/ip_local_port_range') as range_file:
            start, end = range_file.read().strip().split()
            __ip_local_port_range_cache = int(start), int(end)
    return __ip_local_port_range_cache


def available_port():
    """
    Finds free TCP port, this is a shortcut to :py:func:`unoccupied_ports`
    for just one port, in the range of user accessible ports.

    .. warning::

        You should *not* use this utility. Ever. That is because it is impossible to guarantee
        using anything outside the process that the port will be available by the time your application
        tries to bind to it : there is an inherent race condition happening here that we can't solve.
        The proper solution is to bind to port 0 and use ``getsockname(2)`` or its equivalent to make the port
        available to the caller, either through logs or other means, for instance
        :py:meth:`listening_addrs <ets.net.listening_addrs>`.

        If you think you *have* to use this, contact `us <mailto:eti-testing-dev>`_ and we can discuss what is
        best for your use case.

    :return: a port number
    :rtype: ``int``
    """
    return unoccupied_ports(ip_local_port_range(), 1)[0]
