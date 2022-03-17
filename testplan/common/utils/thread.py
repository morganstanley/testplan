"""Threading utilities."""

import time
import threading

from .timing import TimeoutException


def execute_as_thread(
    target,
    args=None,
    kwargs=None,
    daemon=False,
    join=True,
    break_join=None,
    join_sleep=0.01,
    timeout=None,
):
    """
    Execute target callable in a separate thread.

    :param target: Target callable.
    :type target: ``callable``
    :param args: Callable args.
    :type args: ``tuple``
    :param kwargs: Callable kwargs.
    :type kwargs: ``kwargs``
    :param daemon: Set daemon thread.
    :type daemon: ``bool``
    :param join: Join thread before return.
    :type join: ``bool``
    :param break_join: Condition for join early break.
    :type break_join: ``callable``
    :param join_sleep: Join break condition check sleep time.
    :type join_sleep: ``int``
    :param timeout: Timeout duration.
    :type timeout: :py:class:`~testplan.common.utils.timing.TimeoutException`
    """
    thr = threading.Thread(
        target=target, args=args or tuple(), kwargs=kwargs or {}
    )
    thr.daemon = daemon
    thr.start()
    if join is True:
        start_time = time.time()
        while True:
            if not thr.is_alive():
                return
            if break_join is not None and break_join():
                break
            if timeout and time.time() - start_time > timeout:
                raise TimeoutException(
                    "Thread {} timeout after {}s".format(thr, timeout)
                )
            time.sleep(join_sleep)


def interruptible_join(thread, timeout=None):
    """
    Joining a thread without ignoring signal interrupts.

    :param thread: Thread object to wait to terminate.
    :type thread: ``threading.Thread``
    :param timeout: If specified, TimeoutException will be raised if the thread
        does not terminate within the specified timeout.
    :type timeout: ``Optional[numbers.Number]``
    """
    if timeout is None:
        end_time = None
    else:
        end_time = time.time() + timeout

    while end_time is None or time.time() < end_time:
        time.sleep(0.1)
        if not thread.is_alive():
            thread.join()
            break

    if thread.is_alive():
        raise TimeoutException(
            "Thread {thr} timed out after {timeout} seconds.".format(
                thr=thread, timeout=timeout
            )
        )


class Barrier:
    """
    Implements a re-usable, two-phase barrier. Allows a fixed number of threads
    to wait for each other to reach a certain point.

    For python >= 3.2 you can just use
    threading.Barrier instead, this class is provided for
    compatibility with Python 2.

    :param n: Number of threads to wait for at the barrier.
    :type n: ``int``
    """

    def __init__(self, n):
        self.n = n
        self._count = 0
        self._mutex = threading.Lock()
        self._turnstile = threading.Semaphore(0)
        self._turnstile2 = threading.Semaphore(0)

    def wait(self):
        """Wait for all threads to reach the barrier before returning."""
        self._phase1()
        self._phase2()

    def _phase1(self):
        """
        Phase 1: waits for all threads to reach this point and increment the
        count.
        """
        with self._mutex:
            self._count += 1
            if self._count == self.n:
                for _ in range(self.n):
                    self._turnstile.release()

        self._turnstile.acquire()

    def _phase2(self):
        """Phase 2: resets the count so that the barrier can be reused."""
        with self._mutex:
            self._count -= 1
            if self._count == 0:
                for _ in range(self.n):
                    self._turnstile2.release()

        self._turnstile2.acquire()
