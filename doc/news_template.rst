Release Notes
~~~~~~~~~~~~~

.. role:: changed
.. role:: new
.. role:: deprecated
.. role:: removed

.. releaseherald_insert

.. _rev_25.3.0:


25.3.0 (2025-03-25)
-------------------

* :changed:`Changed` Change Testplan exported JSON report structure to reduce report size.

  * Remove unused report entry fields.
      * ``fix_spec_path``.
      * ``status_override`` and ``status_reason`` in case they are empty.
      * ``line_no``, ``code_context`` and ``file_path`` if ``--code`` is not enabled.
      * ``env_status``, ``part``, ``strict_order`` and ``host`` depending on report category.
  * Remove unused assertion entry fields ``category`` and ``flag`` if they are ``DEFAULT``.
  * Merge assertion entry fields ``utc_time`` and ``machine_time`` into a unix timestamp field ``timestamp``, and store timezone info in parent Test-level report under key ``timezone``.
  * Replace ISO 8601 time string with unix timestamp in all ``timer`` fields, and add a ``timezone`` field to Testplan-level report as well.
  * Update data structure of several serialized assertion entries.
      * Delta encode level info of ``flattened_dict`` fields of ``DictLog`` and ``FixLog`` entries.
      * Delta encode level info of ``comparison`` fields of ``DictMatch`` and ``FixMatch`` entries.
      * Delta encode level info of nested ``comparison`` fields of ``DictMatchAll`` and ``FixMatchAll`` entries, remove extra nesting of ``matches`` as well.
      * Preserve abbreviations of match status of ``DictMatch``, ``FixMatch``, ``DictMatchAll`` and ``FixMatchAll`` entries, i.e. ``p`` instead of ``Passed``, ``f`` instead of ``Failed``, ``i`` instead of ``Ignored``.
      * Remove ``indices`` field of ``TableLog`` entries.

* :changed:`Changed` Fix releaseherald documentation
* :deprecated:`Deprecated` Support for Python 3.7 and 3.8 is deprecated and will be removed soon.
* :changed:`Changed` Handle potential race condition during resource monitor termination
* :changed:`Changed` Improve error logging for :py:class:`~testplan.common.remote.remote_service.RemoteService`; fix incorrect imitated workspace on remote due to leftover symlink from previous run.
* :changed:`Changed` Remove Sphinx and other packages for building document from Testplan's dependencies.
* :changed:`Changed` Copy permission bits for the copied binary in App.

.. _rev_25.1.0:


25.1.0 (2025-01-20)
-------------------

* :changed:`Changed` Checks if a process exists by reading the `/proc/<pid>/stat`.
* :changed:`Changed` Support :py:class:`RemoteDriver <testplan.common.remote.remote_driver.RemoteDriver>` in dependency graph of test environment (the ``dependencies`` parameter).
* :changed:`Changed` Use lazy import for Matplotlib and move cache to runpath.
* :new:`New` Added ``--code`` flag to collect code context for the assertions. Code context one-liner will be displayed on the web UI if enabled.
  Note that file path information is no longer collected by default. To collect file path information, enable code context.
* :new:`New` Add a new summary page on resource view to show the task allocation per host.
* :changed:`Changed` Refactor the stop logic of :py:class:`App <~testplan.testing.multitest.driver.app.App>` driver for faster environment shutdown. Rename parameter ``sigint_timeout`` to ``stop_timeout``. Add a new parameter ``stop_signal`` for custom stop signals, its default value ``None`` invokes ``terminate`` method to stop subprocess, i.e. sending ``SIGTERM`` signal to subprocess on Linux.
  **Environment will fail to stop if subprocess doesn't terminate within the default 5-second** ``stop_timeout`` **for graceful shutdown**. Increase ``stop_timeout`` or change ``stop_signal`` (to maybe ``SIGKILL`` on Linux) could resolve this issue.
* :changed:`Changed` Make sure when stop() is called on App type driver, we clean up all orphaned processes.

* :changed:`Changed` If :py:class:`App <~testplan.testing.multitest.driver.app.App>` driver times out during shutdown or leaves orphaned processes after shutdown, Testplan will now emit a warning and perform a forced cleanup instead of failing the tests.
* :changed:`Changed` Increase the number of Remote worker setup thread.
* :changed:`Changed` Fix interactive mode crashing issue when loading a namespace package. (It is still not supported to reload namespace packages.) ``SyntaxError`` will no longer be suppressed during interactive mode code reloading.
* :changed:`Changed` Fix incorrect early stop detection logic.
* :changed:`Changed` Swapped Run and Reload buttons on the interactive UI by user request.
* :changed:`Changed` Use a new JSON library ``orjson`` to improve performance when using Python 3.8 or later versions.
* :changed:`Changed` Limit the length of parameterization testcase name to 255 characters. If the name length exceeds 255 characters, index-suffixed names (e.g., ``{func_name} 1``, ``{func_name} 2``) will be used.
* :new:`New` Testplan now includes its own version in generated report.
* :changed:`Changed` ``JSONExporter`` will log a "file not found" warning in the log instead of raising an exception.
* :changed:`Changed` Fixed an issue where enabling Status icons crashed the report when a test was marked as XFAIL.
* :changed:`Changed` Update ``orjson`` dumping option to allow serializing ``numpy`` objects.

.. _rev_24.9.2:


24.9.2 (2024-09-13)
-------------------

* :new:`New` First official pypi release.
