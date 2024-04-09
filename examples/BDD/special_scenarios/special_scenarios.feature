
Feature: Special Scenarios example

    setup/teardown: Running after before/after the normal scenarios in the Feature file
                    These functions has access to a context, which will be the base context
                    for every scenario runs.

    pre_testcase/post_testcase: Run around any scenario, and has access to the same context
                                as the scenarios


    Scenario Outline: Testcase <name>

        Simple scenario to see that all 3 scenario from here is running
        within the pre/post testcase wrappers

        When we log Hello from Testcase <name>
        Then we log Again Hello from Testcase <name>

        Examples:
            | name  |
            | 1     |
            | 2     |
            | three |

    Scenario: Acces context

        To demonstrate a scenario can access values from context put there by
        setup/pre_testcase

        # check value saved by pre_testcase
        When salute is called with "{{name_from_pre}}"
        Then the result is "Hello Rozi Kis"

        # check value saved by setup
        When salute is called with "{{firstName_from_setup}}"
        Then the result is "Hello Rozi"

    Scenario Outline: Modify context <idx>

        The context prepared in setup is always copied for scenario runs, so
        cahnges to the context does not get persisted between scenarios, even
        though the setup runs just once


        # First check we have the expected values
        When salute is called with "{{name_from_pre}}"
        Then the result is "Hello Rozi Kis"
        When salute is called with "{{firstName_from_setup}}"
        Then the result is "Hello Rozi"

        # Now modify them

        Given "Mari" is stored in the context as firstName_from_setup
        Given "{{firstName_from_setup}} Nagy" is stored in the context as name_from_pre

        When salute is called with "{{name_from_pre}}"
        Then the result is "Hello Mari Nagy"
        When salute is called with "{{firstName_from_setup}}"
        Then the result is "Hello Mari"

        # we run multiple time to see that the modification does not persist
        Examples:
            | idx |
            | 1   |
            | 2   |


    Scenario: setup
        Given "Rozi" is stored in the context as firstName_from_setup
        And we log In setup
        And we log name: {{firstName_from_setup}}

    Scenario: teardown
        And we log In teardown
        And we log name: {{firstName_from_setup}}

    Scenario: pre_testcase
        Given "{{firstName_from_setup}} Kis" is stored in the context as name_from_pre
        And we log In pre_testcase
        And we log name: {{name_from_pre}}

    Scenario: post_testcase
        And we log In post_testcase
        And we log name: {{firstName_from_setup}}
        And we log name: {{name_from_pre}}
