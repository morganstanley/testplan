@KNOWN_TO_FAIL:All_testcase_of_this_feature_is_known_to_fail
@unit
Feature: sum adding two number The wrong way expected to fail

    Scenario: add 1 and -1

        Check if 1-1 == 1

        Given we have two number: 1 and -1
        When we sum the numbers
        Then the result is: 1

    Scenario: add 1 and -2

        Check if 1-2 == 1

        Given we have two number: 1 and -2
        When we sum the numbers
        Then the result is: 1