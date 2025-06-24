Upgrade ``gherkin-official`` to ``32`` for supporting BDD on Python 3.11 or later.

Note that spaces are no longer allowed in gherkin tags, **this could be a breaking change for BDD users.** As a result, lines like ``@tag a @tag b`` in feature files should be replaced with line like ``@tag_a @tag_b``, and line ``@KNOWN_TO_FAIL: some reason`` could be replaced with ``@KNOWN_TO_FAIL:some_reason``.