Move the ``return`` in :func:`run_exporter` out of its ``finally`` block. Python 3.14 emits a
``SyntaxWarning`` for this construct, and the ``return`` silently discarded any ``BaseException``
(e.g. ``KeyboardInterrupt``) raised while an exporter was running.
