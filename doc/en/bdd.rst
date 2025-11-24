.. _bdd_doc:

BDD
***

:py:mod:`testplan.testing.bdd` package makes it possible to use `Gherkin <https://cucumber.io/docs/gherkin/>`_ to express testcases. Testplan can execute test suites expressed in feature files.

Quick Start
===========

Create the following files in your project, or get started using the :ref:`downloadable example <example_bdd_quick_start>`.

``features/first.feature``

.. literalinclude:: ../../examples/BDD/quickstart/features/first.feature

``features/steps/steps.py``

.. literalinclude:: ../../examples/BDD/quickstart/features/steps/steps.py

``test_plan.py``

.. literalinclude:: ../../examples/BDD/quickstart/test_plan.py

Now you should have a project structure like below::

    > tree
    .
    |-- features
    |   |-- first.feature
    |   `-- steps
    |       `-- steps.py
    `-- test_plan.py


Give it a go

.. code-block:: bash

    ./test_plan.py


You should see something like this::

            [Given we have two number: 1 and 1] -> Passed
            [When we sum the numbers] -> Passed
            [Then the result is: 2] -> Passed
          [1 + 1] -> Passed
            [Given we have two number: 2 and 2] -> Passed
            [When we sum the numbers] -> Passed
            [Then the result is: 4] -> Passed
          [2 + 2] -> Passed
        [Example Gherkin Testsuite] -> Passed
      [Example Gherkin Test] -> Passed
    [Example Gherkin Testplan] -> Passed



Basics
======

As in most Gherkin based BDD frameworks, the English written sentences, Given/When/Then ..., need to be turned into code. We call the sentences as **steps**, and the code they trigger as **step definitions**. To match steps with their definition, there are certain rules on directory layout and/or naming. We use code tree layout instead of explicitly setting connection in code, to reduce the boilerplate every Testplan need to have.

The directory structure should look like::

    tree
    .
    |-- features
    |   |-- first.feature
    |   |-- second.feature
    |   |-- important
    |   |   `-- another_feature
    |   `-- steps
    |       |-- first_steps.py
    |       |-- second_steps.py
    |       `-- common_steps.py
    `-- testplan.py

The feature files can be organized into folders, though the structure does not have any meaning in the test execution. There can be as many step definition files as needed.

Using the factory
-----------------

In current state of the BDD framework, it provide a factory that can transform feature files and step definitions into proper :ref:`Multitest <multitest>` testsuites.

:py:class:`BDDTestSuiteFactory(features_path, resolver=NoopContextResolver(), default_parser=RegExParser) <testplan.testing.bdd.BDDTestSuiteFactory>`

- ``features_path``: is the path to the directory containing the feature and step definition
- ``resolver``: there is a simple way to refer data from context. See []()
- ``default_parser``: see [Parsers](#parsers) (``SimpleParser`` or ``RegExParser``)
- ``feature_linked_steps``: see [Step Definitions](#step-definitions)


Standard Gherkin Features
=========================

`This Gherkin Reference <https://cucumber.io/docs/gherkin/reference>`_ should help to start with Gherkin, but the important standard features, and how they translate to Testplan will be discussed here.

Features and Scenarios
----------------------

Features maped to Testsuites and Scenarios are maped to Testcases, having this mapping enable to nicely mix BDD style with Testplan style within the same test.

Scenario Outlines
-----------------

AKA parametrized tests. The ``<placeholders>`` in step definition as well as in the outline name, or documentation text will be filled from the tables under the Example keyword. Each row is generating separate testcase from the outline. *NOTE: Scenario Outlines are not converted to parametrized testcases, but separate testcases will be generated instead*. There can be multiple Example section and they can have different names, which will be reflected in the report.

.. code:: gherkin

    Scenario Outline: add two number (<a> + <b>)

        Check if sum can add two number

        Given we have two number: <a> and <b>
        When we sum the numbers
        Then the result is: <expected>

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

Downloadable example is :ref:`here <example_bdd_scenario_outline>`

Background
-----------

The Feature can have a Background section, which will be executed before each Scenario

.. code:: gherkin

    Background:
        Given: we have an empty DB

    Scenario: add a name to the DB
        When we add new name to the DB
        Then the db has exactly one name in it
    
    Scenario: add another name to the DB
        When we add new name to the DB
        Then the db has exactly one name in it    

both expectation should pass as the Background creating an empty DB for the test

Downloadable example is :ref:`here <example_bdd_background>`

Scenario Description
--------------------

Scenario and Example descriptions are extracted and inserted into the report

.. code:: gherkin

    Scenario Outline: add two number (<a> + <b>)

            Document your scenario here it worth it

            Given we have the avove doc
            When the test run
            Then the report contains the doc

Step arguments
--------------

Steps can get arguments either in python docstring format or in Gherkin data table format

.. code:: gherkin

    Scenario: Arguments

    Given the DB has the following data:
        | name | phone number |
        | John | +361234564   |
        | Jane | +361234561   |
        | Max  | unknown      |
    When I initiate call to Max 
    Then I got the following error:
    """
       <H1>Error</H1>
       The phone number for Max is unknown
    """

the table or the string is passed to the function executed by the step

Downloadable example is :ref:`here <example_bdd_arguments>`

Labels
------

Features, Scenarios, Scenario Outlines and Examples can get labels, these are available in the Testplan execution as tags, and can be used for testcase selection in a run.

.. code:: gherkin

    @business
    Feature: Important feature

        @smoke
        Scenario: base flow

            Given a business process
            When it is executed
            Then the result is expected

        @parametrized
        Scenario Outline: string reverse does not change length

            Given we have a string "<input>"
            When we reverse it
            Then the result has the same <expected>

            @short @table
            Example: short string
            | input | expected |
            | al    | 2        |
            | als   | 3        |

            @slong @table
            Example: long string
            | input      | expected |
            | 1234567890 | 10       |
            | 1234567890 | 20       |

Downloadable example is :ref:`here <example_bdd_labels>`

Non standard Gherkin Features
=====================================
Special Scenarios (setup/teardown)
----------------------------------

There are 4 scenario names, which are treated specially. They do not considered as testcases though the same bdd technics can be used to describe them. They are captured by testplan and are run at the right time to set up initial state and clean up after the test case/suite.

* ``setup``: executed before anything in the feature file
* ``pre_testcase``: executed before every testcase in the feature file
* ``post_testcase``: executed after every testcase in the feature file
* ``teardown``: executed after the whole feature file executed

.. code::  gherkin

    @setup_teardown
    Feature: setup teardown example

        Scenario Outline: Testcase <name>

            When we log Hello from Testcase <name>
            Then we log Again Hello from Testcase <name>

            Examples:
                | name  |
                | 1     |
                | 2     |
                | three |

        Scenario: setup
            And we log In setup

        Scenario: teardown
            And we log In teardown

        Scenario: pre_testcase
            And we log In pre_testcase

        Scenario: post_testcase
            And we log In post_testcase

Downloadable example is :ref:`here <example_bdd_special_scenarios>`

KNOWN_TO_FAIL
-------------

This feature is a direct hook to the Testplan feature: :ref:`Xfail <Xfail>`

One can mark a Feature or Scenario with the ``@KNOWN_TO_FAIL`` label when not possible to fix the code immediately and make the test pass. This make the test pass till it realy fails and make it failed when it start to pass to signify that the label can be removed from it. The handling of this tag is rather special it can carry some reasoning, why is it ok the test to fail. The format is ``@KNOWN_TO_FAIL:reason``.

An example:

.. code:: gherkin

    Feature: sum adding two number The wrong way

        @KNOWN_TO_FAIL:A_simple_Fail_with_Jira
        Scenario: add 1 and -2

            Check if 1-2 == 1

            The jira may change to be closed the find a new one please

            Given we have two number: 1 and -2
            When we sum the numbers
            Then the result is: 1

Downloadable example is :ref:`here <example_bdd_known_to_fail>`

.. _bdd_parallel:

Parallel execution
------------------

Testplan is capable of run testcases parallel within a suite, this feature is available through BDD as well.
The Scenarios, Scenario Outlines or even Examples can be marked with the special ``@TP_EXECUTION_GROUP`` label together
with an execution group name. Scenarios having the same execution_group will be running parallel

In the following example the positive cases will be running parallel:

.. code:: gherkin

    Feature: Parallel execution example

        Scenario Outline: add two number

            Check if sum can add two number

            Given we have two number: <a> and <b>
            When we sum the numbers
            Then the result is: <expected>

            @TP_EXECUTION_GROUP:group1
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


More detailed docs on :ref:`testcase_parallelization`
Downloadable example is :ref:`here <example_bdd_parallel>`

{{mustache}} context resolution
-------------------------------

You can pass contextual data between your sentences in the context paramter pased to each step definition. Some times it is beneficial to even refer values from the context in your actual step definition. To do this you need to add a `ContextResolver` instance to your `BDDTestSuiteFactory`:

.. code:: python
    
    demo_factory = BDDTestSuiteFactory(os.path.join(base_path, 'demo'), ContextResolver())


Then you can access the content of the `conext.field_name` with `{{field_name}}` in your feature file.

.. code:: gherkin

    @resolve @smoke
    Feature: Hello world with random names
        
        Simple hello world example where the name is resolved from  context

        Scenario: double name

            Given a random name as firstName
            Given a random name as middleName
            When salute is called with "{{firstName}} {{middleName}}"
            Then the result is "Hello {{firstName}} {{middleName}}"


Two execution of the above can be seen below, please note that we generate the names in random, but still visible in the step definition::

      [Given a random name as firstName] -> Passed
      [Given a random name as middleName] -> Passed
      [When salute is called with "Marvin John"] -> Passed
      [Then the result is "Hello Marvin John"] -> Passed
    [double name] -> Passed

      [Given a random name as firstName] -> Passed
      [Given a random name as middleName] -> Passed
      [When salute is called with "Jane Marvin"] -> Passed
      [Then the result is "Hello Jane Marvin"] -> Passed
    [double name] -> Passed


The context resolver can resolve values from nested indexable structures (maps,lists) with dot notation ``{{person.name.lastName}}`` where ``person`` is a dictionary in the context, which has a ``name`` key in it, which is again a dictionary having ``lastName`` key in it. This also works with lists: ``myList.2.name`` refer to the ``name`` item of the 3rd dictionary in ``myList``. This works out of the box for any indexable object, with the following ``Indexable`` mixin any user defined class can make indexable as the below example shows:

.. code:: python

    class Indexable:
        def __getitem__(self, item):
            return self.__dict__[item]

    class indexexample(Indexable):

        def __init__(self):
            self.a = 12
            self.b = 13

    context.i = indexexample()


in the fature files ``{{i.a}} == 12`` and ``{{i.b}} == 13``

Downloadable example is :ref:`here <example_bdd_context_resolution>`

Step Definitions
================

There are two ways to provide step definitions, by default step definitions should be in the feature directory under steps subdir. All ``.py`` files are loaded by the factory. In this form all scenarios can refer all step definitions within all the `.py` files. This also mean if two step definition match for the same sentence, only the one will be running, which one, do not make any assumption on it.

Alternative way is to use feature files linked steps. To use this mode the factory should be created with ``feature_linked_steps=True`` In this mode each ``*.feature`` file need to have a ``*.steps.py`` pair next to it. Each feature file has it's own set of steps so one can do different thing for the same sentence in different features. All :ref:`downloadable BDD examples <example_bdd>`, except QuickStart is written in this way.

To have common steps in either mode it is possible to import step definition to other step definitions, see:  :ref:`Import step definitions <import_step_definitions>`

Step definitions are just functions which are decorated with the `@step` decorator (for convenience ``@Given``, ``@When``, ``@Then``, ``@And``, ``@But`` also provided). The parameter of the decorator is either a string which describe the match or a :py:class:`testplan.testing.bdd.parsers.Parser` which can match strings.

The step functions should take at least 3 parameters:

* ``env``: The same environment as in Multitest testcase. You have access to the drivers, for an example check: :ref:`BDD rewrite <example_bdd_tcp>` of :ref:`the simple tcp <example_tcp>` example
* ``result``: A Result object same way as a Multitest testcase
* ``context``: which is a dictionary like object. There is a separate contex for each Scenarion at runtime. Step definitions can use the context object to store/pass state between each other.

.. code:: python

    @step('say Hello World')
    def step_definition(env, result, context):
        result.log('Hello World')
    
Step Arguments
--------------
Step arguments can be captured in the step definition as well, in this case a 4th argument will be passed to the step definition

.. code:: gherkin

    Scenario: 
        When say:
        """
        Hello World
        """


.. code:: python
    
    @step('say:')
    def step_definition(env, result, context, arg):
        result.log(arg)
    
Downloadable example is :ref:`here <example_bdd_arguments>`

Parameter capture
------------------
Bits and pieces from the sentence can be captured as parameter to the function

.. code:: gherkin
    
    Scenario: 
        When salute to John

With SimpleParser one can just enclose a name to {} and the captured string get passed to the step definition in *kwargs* with the same name. Detailed description of parsers see: :ref:`Parsers <bdd_parsers>`

.. code:: python

    @step(SimpleParser('salute to {name}')
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)


Step argument and Parameter capture can be combined

.. code:: gherkin
    
    Scenario: 
        When salute to John with:
        """
        Hello
        """

Downloadable example is in :ref:`parsers example <example_bdd_parsers>`

.. code:: python

    @step(SimpleParser('salute to {name} with')
    def step_definition(env, result, context, arg, name):
        result.log(arg + " " + name)


.. _bdd_parsers:

Parsers
-------

By default the gherkin sentences matched by reg exp to step definitions, which is a powerful way of matching and capturing parameters. Some time it means more complex syntax so there is a much simpler parser to choose. The bellow two step definition doing the same thing: 


.. code:: gherkin
    
    Scenario: 
        When salute to John


.. code:: python

    @step(SimpleParser('salute to {name}'))
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)

    @step(RegExParser('salute to (?P<name>.*)'))
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)


Default Parser can be set on the Factory constructor

.. code:: python

    @test_plan(name="Gherkin Tests")
    def main(plan):
        factory = BDDTestSuiteFactory('features', default_parser=SimpleParser)
        plan.add(MultiTest("GherkinTest", "Example Gherkin Suite", factory.create_suites()))

or within a step definition file with the follwoing way:

.. code:: python

    from testplan.testing.bdd.step_registry import step, set_actual_parser

    # use the simple parser for these definitions
    set_actual_parser(SimpleParser)

    @step('salute to {name}')
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)

    @step(RegExParser('salute to (?P<name>.*)'))
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)


As seen above the default always can be overwritten if passing a parser instead of a string to the decorator. Also if actual_parser is set from that point till it is set again that is the actual parser in the step definition file.

.. code:: python

    from testplan.testing.bdd.step_registry import step, set_actual_parser

    # use the simple parser for these definitions
    set_actual_parser(SimpleParser)

    @step('salute to {name}')
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)

    # and the regex parser for these definitions
    set_actual_parser(RegExParser)
    @step('salute to (?P<name>.*)')
    def step_definition(env, result, context, name):
        result.log('Hello ' + name)

Downloadable example is :ref:`here <example_bdd_parsers>`

.. _import_step_definitions:

Import step definitions
-----------------------
It is possible to import step definition files into another step definition file. This is useful either in feature linked steps mode, when a feature file linked with a single step definition file, but one may have common steps for reuse. Or in the default mode, when several top level tests are defined, but some steps are used in several top level tests. The ``step_registry`` package has a method ``import_steps(path_to_package)``. The path should be relative to the step definition file, that importing the other. Importing multiple step definition is possible, but if steps matchers are the same only one of the steps will be executed. See example below:

``one.feature``

.. code:: gherkin

    @feature_linked @smoke
    Feature: Salute in English

        Scenario: Salute

            Given my name is John
            When one salute
            Then I hear: Hello John

`one.steps.py`

.. code:: python

    from testplan_bdd.step_registry import When, import_steps

    import_steps('common.py')

    @When('one salute')
    def step_definition(env, result, context):
        context.salute = 'Hello {}'.format(context.name)

`common.py`

.. code:: python

    from testplan_bdd.step_registry import Given, Then


    @Given('my name is {name}')
    def step_definition(env, result, context, name):
        context.name = name

    @Then('I hear: {salute}')
    def step_definition(env, result, context, salute):
        result.equal(salute)(context.salute)

Downloadable example is :ref:`here <example_bdd_import_steps>`

.. _common_step_definitions:

Common step definitions
-----------------------
In case of a set of common steps, which are structured in multiple files and need to be shared between BDDTestSuiteFactories, there is an easier way besides importing them into each feature's ``step`` directory, too. One can specify their location by giving their relative path(s) as a list in the ``common_step_dirs`` parameter of the ``BDDTestSuiteFactory`` instance:

For example, let's assume that our directory structure looks like this::

    > tree
    .
    |-- features
    |   |-- feature1
    |   |   |-- steps
    |   |   |   `-- feature1.py
    |   |   |-- feature11.feature
    |   |   `-- feature12.feature
    |   |-- feature2
    |   |   |-- steps
    |   |   |   `-- feature2.py
    |   |   `-- feature2.feature
    |   `-- steps
    |       `-- features.py
    `-- test_plan.py

Steps that are used by all features are defined in the ``features/steps`` directory. Therefore, only those steps that are used by a subset of the features need to be defined separately in their corresponding ``steps`` folder, in this example namely in ``features/feature1/steps`` and ``features/feature2/steps``.

.. code:: python

    @test_plan(name="Example Gherkin Testplan")
    def main(plan):
        factory1 = BDDTestSuiteFactory(
            "features/feature1",
            default_parser=SimpleParser,
            common_step_dirs=["features/steps"],
        )
        factory2 = BDDTestSuiteFactory(
            "features/feature2",
            default_parser=SimpleParser,
            common_step_dirs=["features/steps"],
        )
        plan.add(
            MultiTest(
                name="Example Gherkin Test",
                description="Example Gherkin Suites",
                suites=[*factory1.create_suites(), *factory2.create_suites()],
            )
        )

Check the :ref:`downloadable example <example_bdd_common_steps>` for more help.
