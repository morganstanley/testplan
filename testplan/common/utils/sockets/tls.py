import ssl
from abc import ABC, abstractmethod
from os import PathLike
from pathlib import Path
from typing import Optional, Union

OPTIONAL_PATH = Optional[Union[PathLike, str]]


class TLSConfig(ABC):
    """
    Defines the Protocol a TLSConfig need to have
    """

    @abstractmethod
    def get_context(self, purpose: ssl.Purpose) -> ssl.SSLContext:
        """
        The implementation of this function need to return a configured
        :py:class:`~ssl.SSLContext`, example implementations:
        :py:class:`~testplan.common.utils.sockets.tls.DefaultTLSConfig` and
        :py:class:`~testplan.common.utils.sockets.tls.SimpleTLSConfig`


        :param purpose: Either host or client certificate
        :return: should return the configured SSLContext
        """
        ...


class DefaultTLSConfig(TLSConfig):
    """
    This TLSConfig create a default SSLContext as defined in ssl lib

    :param cacert: Optional Root CA certificate
    """

    def __init__(self, cacert: OPTIONAL_PATH = None):
        self.cacert = cacert

    def get_context(self, purpose: ssl.Purpose) -> ssl.SSLContext:
        return ssl.create_default_context(purpose, cafile=self.cacert)


class SimpleTLSConfig(TLSConfig):
    """
    This TLSConfig create SSLContext for host or user auth with the private key and certificate provided

    :param key: path to private key file
    :param cert: path to the certificate path (host or user)
    :param cacert: optional path to the root CA certificate
    """

    def __init__(
        self,
        key: Union[PathLike, str],
        cert: Union[PathLike, str],
        cacert: OPTIONAL_PATH,
    ):
        self.key = Path(key)
        self.cert = Path(cert)
        self.cacert = Path(cacert)

    def get_context(self, purpose: ssl.Purpose) -> ssl.SSLContext:
        context = ssl.create_default_context(
            purpose=purpose, cafile=self.cacert
        )
        context.load_cert_chain(self.cert, self.key)
        return context
