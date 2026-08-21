Fix two macOS-only ``psutil`` failures and run the unit suite on a macOS CI runner.
``TestRunner._is_remote_process_alive`` no longer propagates ``psutil.AccessDenied`` when it
cannot enumerate TCP connections, and the resource monitor only requests ``io_counters`` on
platforms where ``psutil`` implements it.
