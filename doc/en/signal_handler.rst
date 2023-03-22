.. _SIGNAL_HANDLERS:

Signal Handlers
**************

Users can send **usr1** or **usr2** signals to the running testplan process to get some debug information.


Stop for debugging
==================

Triggering **usr1** signal using command ``kill -usr1 <testplan-process-id>`` drops Testplan to a pdb mode.
The command can easily be run from the command line::

    (testplan-env) $ kill -usr1 3456

Sample command line output::

    Received SIGUSR1, dropping into pdb
    --Return--
    > pdb_drop_handler()->None
    -> pdb.set_trace()
    (Pdb)


Print debug information
=======================

Triggering **usr2** signal using command ``kill -usr2 <testplan-process-id>`` prints debug 
information about the testplan process.
The command can easily be run from the command line::

    (testplan-env) $ kill -usr2 3456

Sample command line output::

    Received SIGUSR2, printing current status
    Stack frames of all threads

    # Thread: Thread-1(140632445814528)
    File: "/lib/python3.7/threading.py", line 890, in _bootstrap
    self._bootstrap_inner()
    File: "/lib/python3.7/threading.py", line 926, in _bootstrap_inner
    self.run()
    File: "/lib/python3.7/threading.py", line 870, in run
    self._target(*self._args, **self._kwargs)
    File: "/lib/python3.7/multiprocessing/pool.py", line 110, in worker
    task = get()

    State of tests
    LocalRunner status: STARTED
    No added items in LocalRunner
    No pending items in LocalRunner

    Hosts and number of workers in RemotePool:

    RemotePool MyPool added tasks:
            TCPMultiTest_0
            TCPMultiTest_1
            TCPMultiTest_2
            TCPMultiTest_3

    RemotePool MyPool pending tasks:
            TCPMultiTest_0

    Workers in RemotePool MyPool with status and waiting assigned tasks:
            <Worker 1>
                    Status: active, Reason: None
                    Waiting for completion of tasks: {'TCPMultiTest_0'}

            <Worker 2>
                    Status: active, Reason: None
                    No tasks to complete.
