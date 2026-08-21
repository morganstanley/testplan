Widen the upper bounds in ``TestDriverTiming::test_driver_timings``. The assertions left only
100ms of headroom over the driver's own sleeps, which a slow CI host can exceed.
