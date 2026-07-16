"""Remote worker pool unit tests."""

import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from testplan.runners.pools.remote import RemotePool


def test_early_stop_worker_does_not_wait_for_pool_lock():
    pool = object.__new__(RemotePool)
    pool._pool_lock = threading.Lock()
    worker = SimpleNamespace()
    pool._pool_lock.acquire()

    with ThreadPoolExecutor(max_workers=1) as executor:
        result = executor.submit(pool._early_stop_worker, worker)
        try:
            assert result.result(timeout=1) is False
        finally:
            pool._pool_lock.release()


def test_early_stop_worker_releases_pool_lock():
    pool = object.__new__(RemotePool)
    pool._pool_lock = threading.Lock()
    pool.pool = None
    worker = SimpleNamespace(assigned={"task"})

    assert pool._early_stop_worker(worker) is False
    assert pool._pool_lock.acquire(blocking=False)
    pool._pool_lock.release()
