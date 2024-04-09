Feature: TCP example

    Scenario: setup

        Given the server is accepting connectons

    Scenario Outline: Send/Receive <message> --- <response>
        When client send: <message>
        Then the server receive: <message>

        When the server respond with: <response>
        Then the client got: <response>

        Examples:
        | message | response |
        | Hello   | World    |
        | Test    | Plan     |