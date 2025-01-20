Change Testplan exported JSON report structure to reduce report size.

* Remove unused report entry fields.
    * ``fix_spec_path`` and ``host``.
    * ``status_override`` and ``status_reason`` in case they are empty.
    * ``line_no``, ``code_context`` and ``file_path`` if ``--code`` is not enabled.
    * ``env_status``, ``part`` and ``strict_order`` depending on report category.
* Remove unused assertion entry fields ``category`` and ``flag`` if they are ``DEFAULT``.
* Merge assertion entry field ``utc_time`` and ``machine_time`` into unix-format ``timestamp``, and store timezone info in parent Test-level report under key ``timezone``.
