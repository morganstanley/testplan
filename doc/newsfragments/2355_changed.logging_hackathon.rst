Testplan logging has overseen a major update in terms of log levels, content, and verbosity.

    * New level USER_INFO has been introduced and will replace TEST_INFO, DRIVER_INFO, and EXPORTER_INFO with an ETA of 4/30/2023. WARNING: this requires updating these to USER_INFO.
    * USER_INFO is responsible for baseline execution and progress information.
    * INFO is responsible for more verbose information like driver status changes, connection/disconnection of transports, and so on.
    * DEBUG is responsible for the lowest level of information like messages sent over transport connections, rsync logs, heartbeats.
    * CRITICAL, ERROR, and WARNING are left untouched except for defect fixes.

Given the scope of the change, we expect minor defects in terms of the above (mismatched level, typos), in addition, we expect UX impact and welcome feedback on any of our client facing channels.

    * Testplan Community Teams channel
    * eti-testing-dev@morganstanley.com
