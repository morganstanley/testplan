@has_outline @fast
@KNOWN_TO_FAIL:A_simple_Fail_with_Jira
Feature: Labels Example

    @single
    @KNOWN_TO_FAIL:A_simple_Fail_with_Jira
    Scenario: add 1 and 2
        Given we have two number: 1 and 2
        When we sum the numbers
        Then the result is: 3

    @parametrized
    Scenario Outline: add two number

        Check if sum can add two number

        Given we have two number: <a> and <b>
        When we sum the numbers
        Then the result is: <expected>

        @positive
        @TP_EXECUTION_GROUP:group1
        Examples: when both positive
            | a   | b   | expected |
            | 1   | 1   | 2        |
            | 2   | 2   | 4        |
            | 123 | 321 | 444      |

        @negative
        @KNOWN_TO_FAIL:A_simple_Fail_with_Jira
        Examples: when one negative
            | a    | b   | expected |
            | 1    | -1  | 0        |
            | 2    | -2  | 0        |
            | -123 | 321 | 198      |