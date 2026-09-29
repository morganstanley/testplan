Expose a non-blocking ``ProcessWorker.started_check()`` for readiness polling
without completing the startup lifecycle. The blocking startup path uses the
same check.

Complete asynchronous resource teardown in ``Environment.stop_in_pool()``
without changing the resource's ``async_start`` configuration.

Transfer remote workers' ``sys.path`` files over the existing SSH connection
instead of starting a separate file-transfer process.

Increase the child worker's response timeout from 30 to 60 seconds to tolerate
slow controller responses.
