Feature: Background Example

    This example show how background is executed before each scenario
    This way it is similar to pre_testcase

    Background:
        Given we have first_name as John
        Given we have last_name as Doe

    Scenario: Salute in English
        When we say hi
        Then it sounds: "Hi John Doe"

    Scenario: Salute in Hungarian
        When we say hello
        Then it sounds: "Hello Doe John"
