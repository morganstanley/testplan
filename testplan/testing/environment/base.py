import copy
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from testplan.common.config import UNSET
from testplan.common.entity.base import Environment
from testplan.common.utils.timing import TimeoutException, TimeoutExceptionInfo
from testplan.testing.environment.graph import DriverDepGraph

if TYPE_CHECKING:
    from testplan.testing.base import Test

MINIMUM_CHECK_INTERVAL = 0.1


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

    def __post_init__(self):
        if self.interval_cap == 0:
            self.interval_cap = self.curr_interval
            self.multiplier = 1
        else:
            self.multiplier = 2

    def record_start(self):
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


class TestEnvironment(Environment):
    def __init__(self, parent: Optional["Test"] = None):
        super().__init__(parent)

        self.__dict__["_orig_dependency"] = None  # Optional[DriverDepGraph]
        self.__dict__["_rt_dependency"] = None  # Optional[DriverDepGraph]
        self.__dict__["_pocketwatches"] = {}  # Dict[str, DriverPocketwatch]

    def set_dependency(self, dependency: Optional[DriverDepGraph]):
        if dependency is None:
            return

        for d in dependency.vertices.values():
            if (
                d.uid() not in self._resources
                or d is not self._resources[d.uid()]
            ):
                raise ValueError(
                    f"Driver {d} used in `dependencies` parameter "
                    "while not being declared in `environment` parameter."
                )
        for d in self._resources.values():
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

    def start_in_pool(self, *_):
        raise RuntimeError(
            "TestEnvironment.start_in_pool: Would not be invoked by design."
        )

    def stop_in_pool(self, *_):
        raise RuntimeError(
            "TestEnvironment.stop_in_pool: Would not be invoked by design."
        )

    def start(self):
        """
        Start the drivers either in the legacy way or following dependency.
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

        while not self._rt_dependency.all_drivers_processed():
            # schedule new drivers
            for driver in self._rt_dependency.drivers_to_process():
                try:
                    self._pocketwatches[driver.uid()].record_start()
                    driver.start()
                except Exception:
                    self._record_resource_exception(
                        message="While starting driver {resource}:\n"
                        "{traceback_exc}\n{fetch_msg}",
                        resource=driver,
                        msg_store=self.start_exceptions,
                    )
                    # exception occurred, skip rest of drivers
                    self._rt_dependency.purge_drivers_to_process()
                    self._rt_dependency.mark_processing(driver)
                    self._rt_dependency.mark_failed_to_process(driver)
                    break
                else:
                    self._rt_dependency.mark_processing(driver)

            # check current drivers
            for driver in self._rt_dependency.drivers_processing():
                watch: DriverPocketwatch = self._pocketwatches[driver.uid()]
                try:
                    if time.time() >= watch.start_time + watch.total_wait:
                        # we got a timed-out here
                        raise TimeoutException(
                            f"Timeout when starting {driver}. "
                            f"{TimeoutExceptionInfo(watch.start_time).msg()}"
                        )
                    res = None
                    if watch.should_check():
                        res = driver.started_check()
                    if res:
                        driver._after_started()
                        driver.logger.info("%s started", driver)
                        self._rt_dependency.mark_processed(driver)
                except Exception:
                    self._record_resource_exception(
                        message="While waiting for driver {resource} to start:\n"
                        "{traceback_exc}\n{fetch_msg}",
                        resource=driver,
                        msg_store=self.start_exceptions,
                    )
                    # exception occurred, skip rest of drivers
                    # continue here as we tend to have fully started drivers
                    self._rt_dependency.purge_drivers_to_process()
                    self._rt_dependency.mark_failed_to_process(driver)

            time.sleep(MINIMUM_CHECK_INTERVAL)

    def stop(self, is_reversed=False):
        """
        Stop drivers while skipping previously skipped ones.
        """
        if self._orig_dependency is None:
            return super().stop(is_reversed=is_reversed)

        # schedule driver stopping in "reverse" order
        self._rt_dependency: DriverDepGraph = self._orig_dependency.transpose()

        # filter drivers based on status
        for driver in self._resources.values():
            if driver.status == driver.status.NONE:
                self._rt_dependency.remove_vertex(id(driver))

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

        while not self._rt_dependency.all_drivers_processed():
            # schedule new drivers
            for driver in self._rt_dependency.drivers_to_process():
                try:
                    self._pocketwatches[driver.uid()].record_start()
                    driver.stop()
                except Exception as e:
                    self._record_resource_exception(
                        message="While stopping driver {resource}"
                        ":\n{traceback_exc}\n{fetch_msg}",
                        resource=driver,
                        msg_store=self.stop_exceptions,
                    )
                    # driver status should be STOPPED even it failed to stop
                    driver.force_stop()
                    driver.logger.info("%s force stopped", driver)
                    self._rt_dependency.mark_processing(driver)
                    self._rt_dependency.mark_failed_to_process(driver)
                else:
                    self._rt_dependency.mark_processing(driver)

            # check current drivers
            for driver in self._rt_dependency.drivers_processing():
                watch: DriverPocketwatch = self._pocketwatches[driver.uid()]
                try:
                    if driver.stopped_check_with_watch(watch):
                        driver._mark_stopped()
                        driver.logger.info("%s stopped", driver)
                        self._rt_dependency.mark_processed(driver)
                except Exception:
                    self._record_resource_exception(
                        message="While waiting for driver {resource} to stop:\n"
                        "{traceback_exc}\n{fetch_msg}",
                        resource=driver,
                        msg_store=self.stop_exceptions,
                    )
                    # driver status should be STOPPED even it failed to stop
                    driver.force_stop()
                    driver.logger.info("%s force stopped", driver)
                    self._rt_dependency.mark_failed_to_process(driver)

            time.sleep(MINIMUM_CHECK_INTERVAL)
