Feature: Hello world with random names

    Simple hello world example where the name is resolved from context

    Scenario: single name

        Use a random name in steps through contex

        # this generate a random name and store in context.name
        Given a random name as name

        # {{name}} will be replaced from context before matching the step definition
        When salute is called with "{{name}}"
        Then the result is "Hello {{name}}"


    Scenario: double name

        Use two random names with the the same steps as before

        Given a random name as firstName
        Given a random name as middleName
        When salute is called with "{{firstName}} {{middleName}}"
        Then the result is "Hello {{firstName}} {{middleName}}"

    Scenario: with argument

        Resolution works in Arguments as well

        Given a random name as name
        When salute is called with:
            """
            Mr/Ms {{name}}
            """
        Then the result is "Hello Mr/Ms {{name}}"

    Scenario: with table

        Works even if the argument is a table

        Given a random name as firstName
        Given a random name as middleName
        When salute is called with names:
            | [firstname]   | [middlename]   |
            | {{firstName}} | {{middleName}} |
        Then the result is "Hello {{firstName}} {{middleName}}"


    Scenario: with dict table
        Given a random name as firstName
        Given a random name as middleName
        When salute is called with name parts:
            | [key]     | [value]        |
            | firstname | {{firstName}}  |
            | midname   | {{middleName}} |
            | lastname  | Smith          |
        Then the result is "Hello {{firstName}} {{middleName}} Smith"

    Scenario: With nested structure
        Given a json document as person:
            """
                {
                    "name": {
                        "firstName": "John",
                        "lastName": "Doe"
                    },
                    "dateOfBirth": "1911 November"
                }
            """
        When salute is called with "{{person.name.firstName}} {{person.name.lastName}} from {{person.dateOfBirth}}"
        Then the result is "Hello {{person.name.firstName}} {{person.name.lastName}} from {{person.dateOfBirth}}"
