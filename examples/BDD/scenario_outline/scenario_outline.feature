Feature: Scenario Outline Example

    Scenario Outline: add two number

        Check if sum can add two number

        Given we have two number: <a> and <b>
        When we sum the numbers
            """
            with a of value <a> and b of value <b>
            """
        Then the result is: <expected>
        And our small table looks good
            | [a] | [b] | [expected] |
            | <a> | <b> | <expected> |

        Examples: when both positive
            | a   | b   | expected |
            | 1   | 1   | 2        |
            | 2   | 2   | 4        |
            | 123 | 321 | 444      |

        Examples: when one negative
            | a    | b   | expected |
            | 1    | -1  | 0        |
            | 2    | -2  | 0        |
            | -123 | 321 | 198      |