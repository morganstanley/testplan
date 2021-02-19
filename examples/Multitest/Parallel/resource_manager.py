"""
Example of a custom driver, that manages several resources. Only a single
resource may be "acquired" at a time, however that same resource may be
acquired multiple times. The manager enforces this logic.
"""
import collections
import functools
import threading

from testplan.testing.multitest import driver


class ExclusiveResourceManager(driver.Driver):
    """
    Driver which manages several resources. Only one resource may be active at a
    time.

    This is only a contrived example to demonstrate the grouping of parallel
    tests execution - not a suggested pattern for managing resources.
    """

    RESOURCE_NAMES = ("first", "second")

    def __init__(self, **kwargs):
        self._refcounts_mutex = threading.Lock()
        self._refcounts = collections.Counter()
        self._resources = {}
        for name in self.RESOURCE_NAMES:
            self.add_resource(name)

        super(ExclusiveResourceManager, self).__init__(**kwargs)

    def __getitem__(self, item):
        """Provide access to the resources."""
        return self._resources[item]

    def add_resource(self, name):
        """Add a named resource."""
        self._resources[name] = _AcquirableResource(
            acquire_callback=functools.partial(self._acquire, name),
            release_callback=functools.partial(self._release, name),
            refcount_callback=functools.partial(self._refcount_cbk, name),
        )

    def _acquire(self, resource_name):
        """
        Check that no other resources are in use. Increment the usage refcount.
        """
        with self._refcounts_mutex:
            if not all(
                count == 0
                for key, count in self._refcounts.items()
                if key != resource_name
            ):
                raise RuntimeError(
                    "Cannot acquire resource {} when other resources are in "
                    "use.".format(resource_name)
                )
            self._refcounts[resource_name] += 1

    def _release(self, resource_name):
        """Decrement the usage refcount."""
        with self._refcounts_mutex:
            assert self._refcounts[resource_name] > 0
            self._refcounts[resource_name] -= 1

    def _refcount_cbk(self, resource_name):
        """Return the current refcount for a given resource."""
        with self._refcounts_mutex:
            return self._refcounts[resource_name]


class _AcquirableResource(object):
    """A resource which may be acquired via a `with` context."""

    def __init__(self, acquire_callback, release_callback, refcount_callback):
        self._acquire_callback = acquire_callback
        self._release_callback = release_callback
        self._refcount_callback = refcount_callback

    def __enter__(self):
        """Report back that this resource has been acquired."""
        self._acquire_callback()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Report back that this resource has been released."""
        self._release_callback()

    @property
    def active(self):
        """:return: whether the resource has been acquired."""
        return self.refcount > 0

    @property
    def refcount(self):
        """:return: the number of active references to this resource."""
        return self._refcount_callback()
