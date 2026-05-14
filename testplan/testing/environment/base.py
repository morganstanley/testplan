import copy
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING, Optional

from testplan.common.config import UNSET
from testplan.common.entity.base import Environment
from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo
from testplan.testing.environment.graph import DriverDepGraph

if TYPE_CHECKING:
    from testplan.testing.base import Test
    from testplan.testing.environment.graph import D

MINIMUM_CHECK_INTERVAL = 0.1
MAX_WORKER_THREADS = 32


@dataclass
class DriverPocketwatch:
    """
    For time tracking for a certain driver. Its implementation must conform
    with what's in testplan.common.utils.timing.
    """

    total_wait: float
    curr_interval: float
    interval_cap: float = 0
    multiplier: float = 0
    start_time: float = 0
    last_check: float = 0

    def __post_init__(self) -> None:
        if self.interval_cap == 0:
            self.interval_cap = self.curr_interval
            self.multiplier = 1
        else:
            self.multiplier = 2

    def record_start(self) -> None:
        self.start_time = time.time()
        self.last_check = self.start_time

    def should_check(self) -> bool:
        curr_time = time.time()
        if curr_time >= self.last_check + self.curr_interval:
            self.last_check = curr_time
            self.curr_interval = min(
                self.curr_interval * self.multiplier, self.interval_cap
            )
            return True
        return False

    @property
    def sleep_interval(self) -> float:
        t = self.curr_interval
        self.curr_interval = min(
            self.curr_interval * self.multiplier, self.interval_cap
        )
        return t


class TestEnvironment(Environment):
    def __init__(self, parent: Optional["Test"] = None):
        super().__init__(parent)

        self.__dict__["_orig_dependency"] = None  # Optional[DriverDepGraph]
        self.__dict__["_rt_dependency"] = None  # Optional[DriverDepGraph]
        self.__dict__["_pocketwatches"] = {}  # Dict[str, DriverPocketwatch]

    def set_dependency(self, dependency: Optional[DriverDepGraph]) -> None:
        if dependency is None:
            return

        d: D
        for d in dependency.vertices.values():
            if (
                d.uid() not in self._resources
                or d is not self._resources[d.uid()]
            ):
                raise ValueError(
                    f"Driver {d} used in `dependencies` parameter "
                    "while not being declared in `environment` parameter."
                )
        for d in self._resources.values():  # type: ignore[assignment]
            if d.cfg.async_start != UNSET:
                raise ValueError(
                    f"`async_start` parameter of driver {d} should not "
                    "be set if driver dependency is specified."
                )
            # we are in a (specially) managed environment, override
            # `async_start`
            d.async_start = True
            if id(d) not in dependency.vertices:
                dependency.add_vertex(id(d), d)

        self._orig_dependency = dependency

    def start_in_pool(self, *_: Any) -> None:
        raise RuntimeError(
            "TestEnvironment.start_in_pool: Would not be invoked by design."
        )

    def stop_in_pool(self, *_: Any) -> None:
        raise RuntimeError(
            "TestEnvironment.stop_in_pool: Would not be invoked by design."
        )

    def _run_single_driver_start(
        self, driver: "D", watch: DriverPocketwatch
    ) -> None:
        """
        Worker invoked in a per-driver thread. Triggers driver start (which
        returns quickly because `async_start=True`), then polls
        ``started_check`` paced by ``watch`` until the driver is ready or a
        timeout occurs. Records exceptions into ``self.start_exceptions``.

        Raises no exception; failure is signalled by recording into the
        exception store and returning.
        """
        try:
            watch.record_start()
            driver.start()
        except Exception:
            self._record_resource_exception(
                message="While starting driver {resource}:\n"
                "{traceback_exc}\n{fetch_msg}",
                resource=driver,  # type: ignore[arg-type]
                msg_store=self.start_exceptions,
            )
            raise _DriverStartFailure()

        try:
            while True:
                time.sleep(watch.sleep_interval)
                res = driver.started_check()
                if res:
                    # TODO: with thread-based impl this scenario should barely
                    # TODO: happen, need to remove this branch later
                    if time.time() >= watch.start_time + watch.total_wait:
                        driver.logger.error(
                            "Timeout when starting %s despite"
                            " it's probably started now. %s",
                            driver,
                            TimeoutExceptionInfo(watch.start_time).msg(),
                        )
                    driver._after_started()
                    driver.logger.info("%s started", driver)
                    return
                if time.time() >= watch.start_time + watch.total_wait:
                    raise TimeoutException(
                        f"Timeout when starting {driver}. "
                        f"{TimeoutExceptionInfo(watch.start_time).msg()}"
                    )
        except Exception:
            self._record_resource_exception(
                message="While waiting for driver {resource} to start:\n"
                "{traceback_exc}\n{fetch_msg}",
                resource=driver,  # type: ignore[arg-type]
                msg_store=self.start_exceptions,
            )
            raise _DriverStartFailure()

    def _run_single_driver_stop(
        self, driver: "D", watch: DriverPocketwatch
    ) -> None:
        """
        Worker invoked in a per-driver thread. Triggers driver stop, then
        polls ``stopped_check_with_watch`` until the driver has stopped or
        a timeout occurs. Records exceptions and force-stops the driver
        on failure.

        Raises ``_DriverStopFailure`` to signal a failure to the orchestrator.
        ---
        personally i don't quite like the idea of stopped_check_with_watch,
        but i don't come up with a better way
        """
        try:
            watch.record_start()
            driver.stop()
        except Exception:
            self._record_resource_exception(
                message="While stopping driver {resource}"
                ":\n{traceback_exc}\n{fetch_msg}",
                resource=driver,  # type: ignore[arg-type]
                msg_store=self.stop_exceptions,
            )
            driver.force_stop()
            driver.logger.info("%s force stopped", driver)
            raise _DriverStopFailure()

        try:
            while True:
                time.sleep(watch.sleep_interval)
                # TODO: extra hook on driver to suppress stop timeout?
                if driver.stopped_check_with_watch(watch):
                    driver._mark_stopped()
                    driver.logger.info("%s stopped", driver)
                    return
        except Exception:
            self._record_resource_exception(
                message="While waiting for driver {resource} to stop:\n"
                "{traceback_exc}\n{fetch_msg}",
                resource=driver,  # type: ignore[arg-type]
                msg_store=self.stop_exceptions,
            )
            driver.force_stop()
            driver.logger.info("%s force stopped", driver)
            raise _DriverStopFailure()

    def start(self) -> None:
        """
        Start the drivers either in the legacy way or following dependency.

        When a dependency graph is set, each eligible driver is started in
        its own worker thread (bounded by a per-call thread pool). The
        dependency graph still gates which drivers may begin.
        """
        if self._orig_dependency is None:
            # we got no dependency declared, go with the legacy way
            return super().start()

        # (re)set dependency graph
        self._rt_dependency = copy.copy(self._orig_dependency)

        # distribute pocketwatches
        for _, v in self._rt_dependency.vertices.items():
            if isinstance(v.started_check_interval, tuple):
                curr_interval, interval_cap = v.started_check_interval
                self._pocketwatches[v.uid()] = DriverPocketwatch(
                    v.start_timeout, curr_interval, interval_cap
                )
            else:
                self._pocketwatches[v.uid()] = DriverPocketwatch(
                    v.start_timeout, v.started_check_interval
                )

        n_workers = max(min(MAX_WORKER_THREADS, len(self._rt_dependency)), 1)
        futures: Dict[int, Future] = {}
        scheduling_halted = False
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            while not self._rt_dependency.all_drivers_processed():
                # schedule new drivers (unless a failure has halted scheduling)
                if not scheduling_halted:
                    for driver in self._rt_dependency.drivers_to_process():
                        watch = self._pocketwatches[driver.uid()]
                        futures[id(driver)] = pool.submit(
                            self._run_single_driver_start, driver, watch
                        )
                        self._rt_dependency.mark_processing(driver)

                # check current drivers
                progressed = False
                while not progressed:
                    time.sleep(MINIMUM_CHECK_INTERVAL)
                    for driver in self._rt_dependency.drivers_processing():
                        fut = futures[id(driver)]
                        if not fut.done():
                            continue
                        progressed = True
                        exc = fut.exception()
                        del futures[id(driver)]
                        if exc is None:
                            self._rt_dependency.mark_processed(driver)
                        else:
                            # exception details have already been recorded
                            # by the worker. Halt new scheduling but let
                            # in-flight drivers finish naturally.
                            if not scheduling_halted:
                                self._rt_dependency.purge_drivers_to_process()
                                scheduling_halted = True
                            self._rt_dependency.mark_failed_to_process(driver)

    def stop(self, is_reversed: bool = False) -> None:
        """
        Stop drivers while skipping previously skipped ones.

        When a dependency graph is set, each eligible driver is stopped in
        its own worker thread (bounded by a per-call thread pool), following
        the transposed dependency graph. Failures do not halt scheduling -
        teardown is best-effort across all drivers.
        """
        if self._orig_dependency is None:
            return super().stop(is_reversed=is_reversed)

        # schedule driver stopping in "reverse" order
        self._rt_dependency = self._orig_dependency.transpose()

        # filter drivers based on status
        for resource in self._resources.values():
            if resource.status == resource.status.NONE:
                self._rt_dependency.remove_vertex(id(resource))

        # distribute pocketwatches
        for _, v in self._rt_dependency.vertices.items():
            if isinstance(v.stopped_check_interval, tuple):
                curr_interval, interval_cap = v.stopped_check_interval
                self._pocketwatches[v.uid()] = DriverPocketwatch(
                    v.stop_timeout, curr_interval, interval_cap
                )
            else:
                self._pocketwatches[v.uid()] = DriverPocketwatch(
                    v.stop_timeout, v.stopped_check_interval
                )

        n_workers = max(min(MAX_WORKER_THREADS, len(self._rt_dependency)), 1)
        futures: Dict[int, Future] = {}
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            while not self._rt_dependency.all_drivers_processed():
                # schedule new drivers - unlike start(), failures do not
                # stop scheduling (teardown is best-effort)
                for driver in self._rt_dependency.drivers_to_process():
                    watch = self._pocketwatches[driver.uid()]
                    futures[id(driver)] = pool.submit(
                        self._run_single_driver_stop, driver, watch
                    )
                    self._rt_dependency.mark_processing(driver)

                # check current drivers
                progressed = False
                while not progressed:
                    time.sleep(MINIMUM_CHECK_INTERVAL)

                    for driver in self._rt_dependency.drivers_processing():
                        fut = futures[id(driver)]
                        if not fut.done():
                            continue
                        progressed = True
                        exc = fut.exception()
                        del futures[id(driver)]
                        if exc is None:
                            self._rt_dependency.mark_processed(driver)
                        else:
                            # exception details have already been recorded
                            # by the worker; the driver was force-stopped.
                            self._rt_dependency.mark_failed_to_process(driver)


class _DriverStartFailure(Exception):
    """Internal sentinel raised by start workers to signal failure."""


class _DriverStopFailure(Exception):
    """Internal sentinel raised by stop workers to signal failure."""
