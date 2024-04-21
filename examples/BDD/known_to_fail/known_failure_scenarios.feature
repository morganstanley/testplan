@unit
Feature: sum adding two number The wrong way with xfail scenarios

    @KNOWN_TO_FAIL:
    Scenario: add 1 and -3

        Check if 1-3 == 1

        Given we have two number: 1 and -3
        When we sum the numbers
        Then the result is: 1

    @KNOWN_TO_FAIL: A simple Fail with comment
    Scenario: add 1 and -1


        Check if 1-1 == 1

        Given we have two number: 1 and -1
        When we sum the numbers
        Then the result is: 1


    Scenario Outline: sums

        Check if <num1> + <num2> == <expected>

        Given we have two number: <num1> and <num2>
        When we sum the numbers
        Then the result is: <expected>

        @KNOWN_TO_FAIL: Failing scenario outline examples
        Examples: Failing examples
            | num1 | num2 | expected |
            | 1    | -1   | 1        |
            | 1    | -2   | 1        |
            | 1    | -3   | 1        |

        Examples: Non failing examples
            | num1 | num2 | expected |
            | 1    | -1   | 0        |
            | 1    | -2   | -1       |
            | 1    | -3   | -2       |
