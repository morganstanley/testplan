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
        self.__dict__["_remote_service"] = remote_service
        self.__dict__["_driver_cls"] = driver_cls
        self.__dict__["_options"] = options
        self.__dict__["_handle"] = None

    def _init_handle(self):
        rmt_driver_cls = getattr(
            self._remote_service.rpyc_connection.modules[
                self._driver_cls.__module__
            ],
            self._driver_cls.__name__,
        )
        self._options["runpath"] = "/".join(
            [
                self._remote_service._remote_resource_runpath,
                self._options["name"],
            ]
        )
        self.__dict__["_handle"] = rmt_driver_cls(**self._options)

    def __getattr__(self, name):
        if self._handle is None:
            self._init_handle()
        return getattr(self._handle, name)

    def __setattr__(self, name, value):
        if self._handle is None:
            self._init_handle()
        setattr(self._handle, name, value)
