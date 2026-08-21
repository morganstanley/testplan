Compare against a snapshot of pre-existing child processes in ``test_basic_loose`` instead of
asserting the test process has no children at all. Python's ``multiprocessing`` helpers
(``resource_tracker``, and the forkserver process that Python 3.14 starts by default on Linux)
are children of the interpreter and outlive any single test.
