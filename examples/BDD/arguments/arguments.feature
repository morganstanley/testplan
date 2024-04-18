Feature: Arguments Examples

    Scenario: Docstring

        Given we log a complex formatted string:
            """
            This is a multi line formatted string
                with leading spaces
            expected to be logged as is.
            """

    Scenario: Table Data

        Given we have a table and we nicely log it:
            | name | phone number |
            | John | +361234564   |
            | Jane | +361234561   |
            | Max  | unknown      |

    Scenario: Argument mixed with captured parameters

        Given we fill the format with name: John
            """
            Hello %s
            """
        Then the result is "Hello John"