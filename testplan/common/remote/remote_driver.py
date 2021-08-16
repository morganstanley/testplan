class RemoteDriver:
    """
    A proxy object that forwards access of itself to the actual driver that
    runs on remote host via the remote_service's rpyc connection.
    :param remote_service: the remote_service object to use
    :type remote_service: ``RemoteService``
    :param driver_class: the class of the driver to instantiate on remote host
    :type driver_class: ``class``

    Also takes all driver_class's options.
    """

    def __init__(self, remote_service, driver_cls, **options):

        self.__dict__["rpyc_connection"] = remote_service.rpyc_connection
        self.__dict__["_driver_cls"] = getattr(
            self.rpyc_connection.modules[driver_cls.__module__],
            driver_cls.__name__,
        )

        options["runpath"] = "/".join(
            [remote_service._remote_resource_runpath, options["name"]]
        )

        self.__dict__["_handle"] = self._driver_cls(**options)

    def __getattr__(self, name):
        return getattr(self._handle, name)

    def __setattr__(self, name, value):
        setattr(self._handle, name, value)
