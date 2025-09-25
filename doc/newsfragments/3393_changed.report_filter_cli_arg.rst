Several changes to report filtering command line arguments. **This is a breaking change.**

* Remove command line argument ``--report-filter``, part of its functionality can be achieved using ``--report-exclude`` instead. Please check its help message for more details.
* Remove command line argument ``--omit-skipped``.
* Change the behavior of command line argument ``--omit-passed``, now it preserves passed case entries in the report while omitting their assertions.