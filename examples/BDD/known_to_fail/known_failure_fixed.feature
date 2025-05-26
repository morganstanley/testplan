
Feature: Expected to fail but pass

    This example demonstrate a known to fail scenario which do not fail animore
    so testplan will just fail the test to show that there is something to check

    @KNOWN_TO_FAIL:That_actually_do_not_fail
    Scenario: expected to fail but not failing so failing

        Check if 1-2 == 1

        Given we have two number: 1 and -2
        When we sum the numbers
        Then the result is: -1
