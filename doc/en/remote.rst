.. _Remote:

Remote Driver
=============

This feature starts one or more drivers on a remote host and allows access to
them from tests that run locally. The remote drivers can be manipulated as if
they were local - user can call the driver methods as usual in testcases, only
that the methods are actually executed on remote host.

The implementation of remote driver is based on
`RPyC <https://rpyc.readthedocs.io/en/latest/>`_ library and has some analogies
with :py:class:`~testplan.runners.pools.remote.RemotePool`
(but not to be confused, they are two different features). First the remote host
will be set up for drivers - create runpath, make available of workspace and
dependencies, push user files etc. Then a classic-mode RPyC server will
be started on remote host. The server is abstracted into
:py:class:`~testplan.common.remote.remote_service.RemoteService` class. Once the
remote service is started, we can instantiate
:py:class:`~testplan.common.remote.remote_driver.RemoteDriver` that run remotely
via the remote service.

Please note for now this feature is only tested for Linux(local) to
Linux(remote) use case, we plan to support Windows(local) to Linux(remote)
in future.

A basic example of remote driver can be found :ref:`here <example_remote_driver>`.