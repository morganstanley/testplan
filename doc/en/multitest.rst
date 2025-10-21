.. _MultiTest:

MultiTest
*********

Introduction
============
MultiTest is a functional testing framework. Unlike unit testing frameworks,
it can be used to drive many processes at once, and interact with them from the
outside, for example through tcp connections.

MultiTest testcases are written in `Python <http://www.python.org>`_ and are not
inherently limited to a set of APIs or functionalities. While the library
provides a large amount of drivers and assertions, users can easily provide
their own as well.

For API documentation see the
:py:class:`MultiTest <testplan.testing.multitest.base.MultiTest>` class reference.


Usage
=====
A MultiTest instance can be constructed from the following parameters:

* **Name**: The name is internal to Testplan, and is used as a handle on the
  test, for example when using the ``--patterns`` command line option to filter
  tests, or in the report. It must be unique inside a given Testplan. Note that
  you can select individual testcases in a MultiTest suite by separating them
  from the suite name with a semicolon.
  For example: ``--patterns MultiTestSuite:testcase``.

* **Description**: The description will be printed in the report, below the test
  status. It's a free-form string, spaces and line returns will be displayed as
  they are specified.

* **Suites**: MultiTest suites are simply objects (one or more can be passed)
  that must:

  - be decorated with :py:func:`@testsuite <testplan.testing.multitest.suite.testsuite>`.
  - have one or more methods decorated with
    :py:func:`@testcase <testplan.testing.multitest.suite.testcase>`. @testcase will
    enforce at import time that the method designated as a testcase has the
    following signature:

    .. code-block:: python

      @testcase
      def a_testcase_method(self, env, result):
        ...

  The :py:func:`@testcase <testplan.testing.multitest.suite.testcase>` decorated
  methods will execute in the order in which they are defined. If more than
  one suite is passed, the suites will be executed in the order in which they
  are placed in the list that is used to pass them to the constructor. To
  change testsuite and testcase execution order, click :ref:`here <ordering_tests>`.

* **Environment**: The environment is a list of
  :py:class:`drivers <testplan.testing.multitest.driver.base.Driver>`. Drivers are
  typically implementations of messaging, protocols or external executables. If
  a testcase is intended to test an executable, a driver for that executable
  would typically be defined, as well as drivers for the interfaces that are
  required for interacting with it, such as network connections.

* **Dependencies**: The dependencies is a dict with both keys and values of
  :py:class:`drivers <testplan.testing.multitest.driver.base.Driver>` or
  iterable collection of
  :py:class:`drivers <testplan.testing.multitest.driver.base.Driver>`.
  Drivers on the value side should only start after drivers on the key side are
  fully started. When specified, Testplan will try to schedule more drivers
  starting concurrently based on the dependencies. Drivers included in
  ``environment`` while not presented in ``dependencies`` will be started
  concurrently at the very beginning. Using empty dict here to instruct all
  drivers to start concurrently. Using ``None`` here to specify the legacy
  scheduling with ``async_start`` flags being set. Click :ref:`here <multitest_drivers>`
  for more information.

* **Runtime Information**: The environment always contains a member called
  ``runtime_info`` which contains information about the current state of the
  run. See: :py:class:`MultiTestRuntimeInfo <testplan.testing.multitest.base.MultiTestRuntimeInfo>`

* **Initial Context**: The initial context is an optional way to pass
  information to be used by drivers and from within testcases. When drivers are
  added, they are provided with access to the driver environment that also
  contains the initial_context input. This mechanism is useful to let drivers
  know for example how to connect to other drivers. It is possible to use the
  initial context to pass global values that will be available to all drivers
  during startup and testcases during execution. Example of initial context
  can be found :ref:`here <example_basic_initial_context>`

* **Hooks**: Hooks are used to implement measures that complement the testing
  process with necessary preparations and subsequent actions. See :ref:`example <example_best_practice>`.

  - before_start: Callable to execute before starting the environment.
  - after_start: Callable to execute after starting the environment.
  - before_stop: Callable to execute before stopping the environment.
  - after_stop: Callable to execute after stopping the environment.
  - error_handler: Callable to execute when a step hits an exception.


Example
=======


This is an example MultiTest that will start an environment of three drivers
and execute three testsuites that contain testcases. From within the testcases,
the interaction with the drivers is done with the ``env`` argument.

.. code-block:: python

    @testsuite
    class DriverInteraction(object):

        @testcase
        def restart_app(self, env, result):
            env.converter.restart()
            env.server.accept_connection()
            env.client.restart()

            size = env.server.send_text('hello')
            result.equal('Hello', env.client.receive_text(size=size))

    ...

    MultiTest(name='TestConnections',
              environment=[
                   TCPServer(name='server'),
                   Bridge(name='bridge',
                          binary=os.path.join(os.getcwd(), 'run_bridge.py')),
                   TCPClient(name='client',
                             host=context(converter_name, '{{host}}'),
                             port=context(converter_name, '{{port}}'))
              ],
              suites=[BasicTests(), EdgeCases(), DriverInteraction()])


Many more commented examples are available :ref:`here <download>`.


Testsuites & Testcases
======================

Testsuites are :py:func:`@testsuite <testplan.testing.multitest.suite.testsuite>`
decorated classes that contain
:py:func:`@testcase <testplan.testing.multitest.suite.testcase>` decorated methods that
are representing the actual tests in which assertions are performed.

Multitest accepts a list of testsuites. This may be very useful in case
different suites share the same environment. The lifetime of the drivers in
respect to multiple suites is the following:

    1. Start each driver in the environment in sequence
    2. Run ``Suite1``
    3. Run ``Suite2`` and any others
    4. Stop each driver in reverse order


Name customization
------------------

By default, a testsuite is identified in the report by its class name, and testcase
by its function name. User can specify custom name for testsuite or testcase like this:

    * @testcase(name="My Testcase")
    * @testsuite(name="My Test Suite")
    * @testsuite(name=lambda cls_name, suite: "{} -- {}".format(cls_name, id(suite)))

Example can be found :ref:`here <example_basic_name_customization>`.

To customize names for parametrized testcases another argument ``name_func`` can be
used, refer to the document of :ref:`name_func <parametrization_custom_name_func>`.

Strict order
------------

In a test suite all testcases can be forced to run sequentially, which means, they will
be executed strictly in the order as they were defined, even some :ref:`paralell feature <testcase_parallelization>`
like "shuffling" and "execution group" will not take effect. Specify such a test suite
like this:

    * @testsuite(strict_order=True)

When executed in interactive mode, UI can help user to run testcases one by one,
that is, in a "strict ordered" test suite, only the first testcase can run, after
it finishes its execution then the next testcase is able to run, and there is no
idea to re-run the finished testcases unless the whole test report is reset.
Similarly, you cannot run a test suite if some testcases in it already finish
execution or are running, an error message will be displayed.

Listing
-------

Testplan supports listing of all defined tests by command line or programmatic
means. Test listing is also compatible with test filters and sorters, meaning
you can see how the various filtering / ordering rules would affect your tests,
before actually running your plan.


Command line Listing
++++++++++++++++++++

The simplest usage ``--list`` will list all tests in readable & indented format.

This is also a shortcut for ``--info name``. The output will be trimmed per
suite if number of testcases exceed a certain number (This is most likely to
happen when testcase parametrization is used). ``--info name-full`` argument
will display the full list of all testcases, without trimming the output.

.. code-block:: bash

    $ test_plan.py --list
    Primary
      AlphaSuite
        testcase_a
        testcase_b
        ...


``--info pattern`` argument will list the testcases in a format that is
compatible with the ``--patterns`` and ``--tags`` / ``--tags-all`` arguments.
Again some testcases may be trimmed (per suite) if they exceed a certain number,
and ``--info pattern-full`` argument will display the full list of all testcases
without any trimming the output.

.. code-block:: bash

    $ test_plan.py --info pattern
    Primary
    Primary::AlphaSuite
      Primary::AlphaSuite::testcase_a
      Primary::AlphaSuite::testcase_b
      ...


``--info count`` is a rather short way of listing tests, it will just print out
the list of multitests and the number of testsuites & testcases:

.. code-block:: bash

  $ test_plan.py --info count
  Primary: (2 suites, 6 testcases)
  Secondary: (1 suite, 3 testcases)

``--info json`` dumps many metadata about the testplan with testsuite and testcase locations.
It is useful for tools that want to gain info about tests without running them. It has a
form: ``--info json:/path/to/file.json`` in which case the json is saved to ``/path/to/file.json``
instead of dumping to the stdout.

More examples on command line test listing can be seen
:ref:`here <example_multitest_listing_basic>`.


Programmatic Listing
++++++++++++++++++++

Similar test listing functionality can be achieved by passing test lister
objects to ``@test_plan`` decorator via ``test_lister`` argument:


.. code-block:: python

    from testplan import test_plan
    from testplan.testing.listing import PatternLister

    # equivalent to `--list` or `--info name`
    @test_plan(test_lister=NameLister()):
    def main(plan):
      ....

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.listing import NameLister


    # equivalent to `--info pattern`
    @test_plan(test_lister=PatternLister()):
    def main(plan):
      ....


More examples on programmatic test listing can be seen
:ref:`here <example_multitest_listing_basic>`.


Custom Test Listers
+++++++++++++++++++


A custom test lister can be implemented by subclassing
:py:class:`~testplan.testing.listing.BaseLister` or
:py:class:`~testplan.testing.listing.MetadataBasedLister`

and overriding ``get_output`` method. The difference is that in Old BaseLister style the
``get_output`` is called with all :py:class:`~testplan.testing.base.Test` instance added to the plan
one by one while the MetadataBasedLister case is called with
:py:class:`~testplan.testing.multitest.test_metadata.TestPlanMetadata`, which contains all info
about the testplan.

An example implementation of custom test lister can be seen
:ref:`here <example_multitest_listing_custom>`.



Listers can be registered to be used with the ``--info`` commandline parameter the same way as the built in listers.

The custom lister class should provide:

* it's name either setting the :py:attr:`NAME <testplan.testing.listing.BaseLister.NAME>` or override the
  :py:meth:`name() <testplan.testing.listing.BaseLister.name>` method. This should be an Enum name like ``NAME_FULL``.
  The name will be used to derive the commandline param which is the kebab-case version of the name.
* and it's description either setting the :py:attr:`DESCRIPTION <testplan.testing.listing.BaseLister.DESCRIPTION>` or
  override the :py:meth:`description() <testplan.testing.listing.BaseLister.description>` method

and it need to be registered with :py:data:`testplan.testing.listing.listing_registry` as follows

.. code-block:: python

  from testplan.testing.listing import BaseLister, listing_registry
  from testplan import test_plan

  class HelloWorldLister(BaseLister):

    NAME = "HELLO_WORLD"
    DESCRIPTION = "This lister print Hello World for each multitest"

    def get_output(self, instance):
        return "Hello World"

  listing_registry.add_lister(HelloWorldLister())

  # check --info hello-world
  @test_plan()
  def main(plan):
    ....

the full example can be found :ref:`here <example_multitest_listing_custom_cmd>`.

The MetadataBasedLister types can take not just a name in the ``--info`` but even an uri where the
path will be used as the listing location, and the result is written to a file instead of the stdout.
Currently, the only such lister is ``json``. Example call ``--info josn:/path/to/file.json``

.. warning::

  For filtering / ordering / listing operations, programmatic declarations will
  take precedence over command line arguments, meaning command line arguments
  will **NOT** take on effect if there is an explicit
  ``test_filter``/``test_sorter``/``test_lister`` argument in the ``@test_plan``
  declaration.


Filtering
---------

Testplan provides a flexible and customizable interface for test filtering
(e.g. running a subset of tests). It has built-in logic for *tag* and
*pattern* based test filtering, which can further be expanded by implementing
custom test filters.


Command line filtering
++++++++++++++++++++++

The simplest way to filter tests is to use pattern (``--patterns``) or tag
(``--tags`` / ``--tags-all``) filters via command line options.

For pattern filtering individual tests or sets of tests to run can be selected
by passing their name or a glob pattern, for example ``\*string\*`` will match
all testcases whose name includes string.

Note that for MultiTest, the ``:`` separator can be used to select individual
testsuites and individual testcase methods inside those testsuites;
e.g. ``--patterns MyMultiTest:Suite:test_method``. This can of course be
combined with wildcarding; e.g. ``--patterns MyMultiTest:Suite:test_*`` or
``--patterns MyMultiTest:*:test_*``.

Details regarding the supported patterns can be found
`here <http://docs.python.org/library/fnmatch.html>`_ , they're essentially
identical to traditional UNIX shell globbing.

It is also possible to run tests for particular tag(s) using ``--tags``
or ``--tags-all`` arguments. (e.g. ``--tags tag1 tag-group=tag1,tag2,tag3``).
``--tags`` will run tests that match **ANY** of the tag parameters whereas
``--tags-all`` will only run the tests that match **ALL** tag parameters.

When ``--patterns`` and ``--tags`` parameters are used together, Testplan
will only run the tests that match **BOTH** the pattern and the tag arguments.

View :ref:`tagging` section and :ref:`example_multitest_tagging_filtering`
downloadable examples for more detailed information on tagging and command line
filtering usage.


Programmatic Filtering
++++++++++++++++++++++

It is also possible to filter out tests to be run via programmatic means by
passing a filter object to the ``@test_plan`` decorator as ``test_filter``
argument. This feature enables more complex filtering logic. For the pattern and
tag filters mentioned above, their equivalent programmatic declarations would be:

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.filtering import Tags, Pattern

    # equivalent to `--patterns MyMultiTest:Suite:test_method`
    @test_plan(test_filter=Pattern('MyMultiTest:Suite:test_method')):
    def main(plan):
        ....

    # equivalent to `--tags tag1 tag-group=tag1,tag2,tag3`
    @test_plan(test_filter=Tags({
        'simple': 'tag1',
        'tag-group': ('tag1', 'tag2', 'tag3')
    })):
    def main(plan):
        ....

Programmatic filters can be composed via bitwise operators, so it is possible
to apply more complex filtering logic which may not be supported via command
line options only.

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.filtering import Tags, Pattern

    # equivalent to `--patterns MyMultiTest --tags server'
    @test_plan(test_filter=Pattern('MyMultiTest') & Tags('server')):
    def main(plan):
         ....

    # no command line equivalent, run tests that match the pattern OR the tag
    @test_plan(test_filter=Pattern('MyMultiTest') | Tags('server')):
    def main(plan):
        ....

    # no command line equivalent, run tests that DO NOT match the tag `server`
    @test_plan(test_filter=~Tags('server')):
    def main(plan):
         ....


See some :ref:`examples <example_multitest_tagging_filtering>` demonstrating
programmatic test filtering.


Multi-level Filtering
+++++++++++++++++++++

For more granular test filtering, you can pass test filter objects to MultiTest
instances as well. These lower level filtering rules will override plan level
filters.

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.filtering import Tags, Pattern
    from testplan.testing.multitest import MultiTest

    # Plan level test filter that will run tests tagged with `client`
    @test_plan(test_filter=Tags('client')):
    def main(plan):
        multitest_1 = MultiTest(name='Primary', ...)
        # Multitest level test filter overrides plan level filter and runs
        # tests tagged with `server`
        multitest_2 = MultiTest(name='Secondary', test_filter=Tags('server'))


See some :ref:`examples <example_multitest_tagging_multi>` explaining
multi-level programmatic test filtering.


Custom Test Filters
+++++++++++++++++++

Testplan supports custom test filters, which can be implemented by subclassing
:py:class:`testplan.testing.filtering.Filter <testplan.testing.filtering.Filter>`
and overriding ``filter_test``, ``filter_suite`` and ``filter_case``
methods.

Example implementations can be seen
:ref:`here <example_multitest_tagging_custom_filters>`.


.. _ordering_tests:

Ordering Tests
--------------

By default Testplan runs the tests in the following order:

    * Test instances (e.g. MultiTests) are being executed in the order they are
      added to the plan object with
      :py:meth:`plan.add() <testplan.runnable.base.TestRunner.add>` method.
    * Test suites are run in the order they are added to the test instance via
      ``suites`` list.
    * Testcase methods are run in their declaration order in the testsuite class.

This logic can be changed by use of custom or built-in test sorters.

Command line ordering
+++++++++++++++++++++

Currently Testplan supports only shuffle ordering via command line options.
Sample usage includes:

.. code-block:: bash

    $ test_plan.py --shuffle testcases
    $ test_plan.py --shuffle suites testcases --shuffle-seed 932
    $ test_plan.py --shuffle all

Please see the section on :ref:`shuffling` for more detailed information and
benefits of shuffling your test run order.


Programmatic Ordering
+++++++++++++++++++++

To modify test run order programmatically, we can pass a test sorter instance
to ``@test_plan`` decorator via ``test_sorter`` argument.

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.ordering import ShuffleSorter

    # equivalent to `--shuffle all --shuffle-seed 15.2`
    @test_plan(test_sorter=ShuffleSorter(shuffle_type='all', seed=15.2)):
    def main(plan):
        ....

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.ordering import AlphanumericalSorter

    # no command line equivalent, sort everything alphabetically
    @test_plan(test_sorter=AlphanumericalSorter(sort_type='all')):
    def main(plan):
        ....

More examples explaining programmatic test ordering can be seen
:ref:`here <example_multitest_ordering_basic>`.


Custom Test Sorters
+++++++++++++++++++
A custom test sorter can easily be implemented by subclassing
:py:class:`testplan.testing.ordering.TypedSorter <testplan.testing.ordering.TypedSorter>`
and overriding ``sort_instances``, ``sort_testsuites``, ``sort__testcases``
methods.

An example implementation of custom test sorter can be seen
:ref:`here <example_multitest_ordering_custom>`.


Multi-level Test Ordering
+++++++++++++++++++++++++

For more granular test ordering, test sorters can be passed to MultiTest objects
via ``test_sorter`` argument as well. These lower level ordering rules
will override plan level sorters.

.. code-block:: python

    from testplan import test_plan
    from testplan.testing.ordering import ShuffleSorter, AlphanumericalSorter
    from testplan.testing.multitest import MultiTest

    # Shuffle all testcases of all tests
    @test_plan(test_sorter=ShuffleSorter('testcases')):
    def main(plan):
        multitest_1 = MultiTest(name='Primary',
                                ...)
        # Run test cases in alphabetical ordering, override plan level sorter
        multitest_2 = MultiTest(name='Secondary',
                                test_sorter=AlphanumericalSorter('testcases'),
                                ...)


More examples explaining multi-level programmatic test ordering
can be seen :ref:`here <example_multitest_ordering_multi>`.


.. _shuffling:

Shuffling
---------

Testplan provides command line shuffling functionality via ``--shuffle`` and
``--shuffle-seed`` arguments. These can be used to randomise the order in which
tests are run. We strongly recommend to use them in routine cases.

Why is this useful?

    1. Some bugs may only appear in some states of the application under test.
    2. Some tests may not finish cleanly but because of their position in a
       testsuite that error remains unseen.
    3. Some tests may make assumptions on the availability of data that are only
       valid thanks to other tests being run first.

All these cases can be invisible when tests are always run in the same order.
Randomizing the order in which tests are run can help unmask these issues.

What does it do?
   Given the following tests definitions:

   .. code-block:: python

         @testsuite
         class TestSuite1(object):
             @testcase
             def test11(self, env, result):
                 pass

             @testcase
             def test12(self, env, result):
                 pass

         @testsuite
         class TestSuite2(object):
             @testcase
             def test21(self, env, result):
                 pass
             @testcase
             def test22(self, env, result):
                 pass

         @testsuite
         class TestSuite3(object):
             @testcase
             def test31(self, env, result):
                 pass
             @testcase
             def test32(self, env, result):
                 pass

         @testsuite
         class TestSuite4(object):
             @testcase
             def test41(self, env, result):
                 pass
             @testcase
             def test42(self, env, result):
                 pass

         plan.add(MultiTest(name="A",
                            description="A Description",
                            suites=[TestSuite1(), TestSuite2()]))
         plan.add(MultiTest(name="B",
                            description="B description",
                            suites=[TestSuite3(), TestSuite4()]))


   * ``--shuffle instances`` will shuffle the order in which
     :py:class:`MultiTest <testplan.testing.multitest.base.MultiTest>` instances are
     executed. The following definitions will be executed as ``A`` then ``B`` or
     ``B`` then ``A``, with the order of the suites in each preserved, and the
     order of testcases in suites is also preserved. This is useful if the
     environment is shared between the instances and you want to make sure that
     there is no cross-contamination.


   * ``--shuffle suites`` will preserve the order of the
     :py:class:`MultiTest <testplan.testing.multitest.base.MultiTest>` instances, the
     order of testcases but shuffle the order of the suites inside each
     :py:class:`MultiTest <testplan.testing.multitest.base.MultiTest>` instance. So the
     execution of the above snippet would be for instance:

        A:
          - TestSuite2 : test21, test22
          - TestSuite1 : test11, test12
        B:
          - TestSuite3 : test31, test32
          - TestSuite4 : test41, test42

   * ``--shuffle testcases`` will preserve the order of
     :py:class:`MultiTest <testplan.testing.multitest.base.MultiTest>` instances and
     suites but will change the order of testcases.

        A:
          - TestSuite1 : test12, test11
          - TestSuite2 : test21, test22
        B:
          - TestSuite3 : test32, test31
          - TestSuite4 : test42, test41

   * ``--shuffle all`` will randomise all
     :py:class:`MultiTest <testplan.testing.multitest.base.MultiTest>`, suites and cases.

           B:
             - TestSuite4 : test42, test41
             - TestSuite3 : test32, test31
           A:
             - TestSuite1 : test11, test12
             - TestSuite2 : test21, test22

How can I troubleshoot a problem?

    The goal of ``--shuffle`` being to find out problems only detectable in random
    execution ordering, sometimes one needs to be able to replicate the ordering
    from a past run. When using the ``--shuffle`` option, testplan will output the
    seed with which the randomizer was initialised. Passing that seed back to
    ``--shuffle-seed`` will make sure your tests are run in the order that
    uncovered the problem again. The output looks as follow :
    ``Shuffle seed: 9151.0, to run again in the same order pass --shuffle all --shuffle-seed 9151.0``


.. _tagging:

Tagging
-------

Testplan supports test filtering via tags, which can be assigned to top level
tests via ``tags`` argument (e.g. ``GTest(name='CPP Tests', tags='TagA')``,
``MultiTest(name='My Test', tags=('TagB', 'TagC')``). MultiTest framework also
has further support for suite and testcase level tagging as well.

It's possible to run subset of tests using ``--tags`` or ``--tags-all`` arguments.
The difference between ``--tags`` and ``--tags-all`` is that
``--tags tagA tagB`` will run any test that is tagged with ``tagA`` **OR**
``tagB`` whereas ``--tags-all tagA tagB`` will run tests that are tagged with both
``tagA`` **AND** ``tagB``.

.. note::

    If you apply the same tag value both on suite level and testcase level, the
    tag filtering will still work as expected. However keep in mind that
    applying the same testsuite tag explicitly to a testcase is a redundant
    operation.

There are multiple ways to assign tags to a target:

    * Assign a simple tag: ``@testcase(tags='tagA')``
    * Assign multiple simple tags: ``@testcase(tags=('tagA', 'tagB'))``
    * Assign a named tag: ``@testcase(tags={'tag_name': 'tagC'})``
    * Assign multiple named tags: ``@testcase(tags={'tag_name': ('tagC', 'tagD'), 'tag_name_2': 'tagE'})``

While passing command line arguments use tag values directly for simple tag matches and
``<TAG_NAME>=<TAG_VALUE_1>,<TAG_VALUE_2>...`` convention for named tag matches:

    * Filter on a single simple tag: ``--tags tagA``
    * Filter on multiple simple tags ``--tags tagA tagB``
    * Filter on single named tag: ``--tags tag_name_1=tagC``
    * Filter on multiple named tags: ``--tags tag_name_1=tagC,tagD tag_name_2=tagE``
    * Filter on both simple and named tags: ``--tags tagA tagB tag_name_1=tagC,tagD``

Tag format
++++++++++
Tag values and names can consist of alphanumerical characters, as well as
underscore, dash, parentheses ``_-)(``, and can also contain whitespaces.
However they cannot start or end with these special characters.

    * Valid: ``tagA``, ``tag-A``, ``tag_A``, ``tag()A``, ``'tag A'``
    * Invalid: ``-tagA``, ``tagA_``, ``(tagA)``, ``' tagA '``


Simple tags vs named tags
+++++++++++++++++++++++++
It's up to the developer to decide on the tagging strategy, both simple and
named tags have different advantages:

    * Simple tags are easier to use and have a simpler API, whereas named tagging
      needs a little bit of extra typing.

    * Named tags let you categorize tags into different groups and enables finer
      tuning on test filtering. (E.g run all tests for a particular regulation on
      a particular protocol: ``--tags-all regulation=EMIR protocol=TCP``).

    * Simple tags may cause confusion within different contexts:
      e.g. ``@testcase(tags='slow')``, is this a testcase with slow startup time,
      or does it test a piece of code that runs slowly?

A general piece of advice would be to use simple tags when introducing this
functionality to your tests, and gradually upgrade to named tags after you feel
more comfortable.


Example
+++++++

.. code-block:: python

  # Top level test instance tagging
  my_gtest = GTest(name='My GTest', tags='tagA')

  # Testsuite & test case level tagging

  @testsuite(tags='tagA')
  class SampleTestAlpha(object):

      @testcase
      def method_1(self, env, result):
          ...

      @testcase(tags='tagB')
      def method_2(self, env, result):
          ...

      @testcase(tags={'category': 'tagC')
      def method_3(self, env, result):
          ...

      @testcase(tags='category': 'tagD')
      def method_4(self, env, result):
          ...


  @testsuite(tags='tagB')
  class SampleTestBeta(object):

      @testcase
      def method_1(self, env, result):
        ...

      @testcase(tags=('tagA', 'tagC'))
      def method_2(self, env, result):
        ...

      @testcase(tags={'category': ['tagC', 'tagD'])
      def method_3(self, env, result):
        ...


  my_multitest = MultiTest(
      name='My MultiTest', tags=['tagE', 'tagF']
      suites=[SampleTestAlpha(), SampleTestBeta()])


Runs all testcases from ``SampleTestAlpha`` (suite level match),
``SampleTestBeta.test_method_2``, ``SampleTestBeta.test_method_3``
(testcase level match):

.. code-block:: bash

    $ ./test_plan.py --tags tagA

Runs all tests from both ``SampleTestAlpha`` and ``SampleTestBeta``
(suite level match):

.. code-block:: bash

    $ ./test_plan.py --tags tagA tagB

``--tags-all`` runs the test **if and only if** all tags match. Runs
``SampleTestAlpha.test_method_2``, ``SampleTestBeta.test_method_2``,
``SampleTestBeta.test_method_3``:

.. code-block:: bash

    $ ./test_plan.py --tags-all tagA tagB

Runs ``SampleTestAlpha.test_method_3``, ``SampleTestAlpha.test_method_4``,
``SampleTestBeta.test_method_3``:

.. code-block:: bash

    $ ./test_plan.py --tags category=tagC,tagD

Runs ``SampleTestBeta.test_method_3`` (both tag values must match):

.. code-block:: bash

  $ ./test_plan.py --tags-all category=tagC,tagD

For more detailed examples, see
:ref:`here <example_multitest_tagging_filtering>`.

Tag based multiple reports
++++++++++++++++++++++++++

Multiple PDF reports can be created for tag combinations. See a
:ref:`downloadable example <example_tagged_filtered_pdf>` that demonstrates
how this can be done programmatically and via command line.

.. _parametrization:

Parametrization
---------------

Testplan makes it possible to write more compact testcases via use of
``@testcase(parameters=...)`` syntax. There are 2 types of parametrization:
:ref:`simple <parametrization_simple>` and
:ref:`combinatorial <parametrization_combinatorial>`. In both cases you need to:

    1. Add extra arguments to the testcase method declaration.
    2. Pass either a dictionary of lists/tuples or list of dictionaries/tuples
       as ``parameters`` value.

See also the :ref:`a downloadable example <example_multitest_parametrization>`.


.. _parametrization_simple:

Simple Parametrization
++++++++++++++++++++++

You can add simple parametrization support to a testcase by passing a ``list``/``tuple``
of items as ``parameters`` value. Each item of the tuple must either be:

    * A ``tuple`` / ``list`` with positional values that correspond to the
      parametrized argument names in the method definition.
    * A ``dict`` that has matching keys & values to the parametrized argument names.
    * A single value (that is not a ``tuple``, or ``list``) `if and only if` there
      is a single parametrization argument. This is more of a shortcut for readability.

The ``@testcase`` decorator will generate 2 testcase methods using each element
in the ``parameters`` tuple below:

.. code-block:: python

    @testsuite
    class SampleTest(object):

      @testcase(
          parameters=(
              # Tuple notation, assigns values to `a`, `b`, `expected` positionally
              (5, 10, 15),
              (-2, 3, 1),
              (2.2, 4.1, 6.3),
              # Dict notation, assigns values to `a`, `b`, `expected` explicitly
              {'b': 2, 'expected': 12, 'a': 10},
              {'a': 'foo', 'b': 'bar', 'expected': 'foobar'}
          )
      )
      def addition(self, env, result, a, b, expected):
          result.equal(a + b, expected)
          # The call order for the generated methods will be as follows:
          # result.equal(5 + 10, 15)
          # result.equal(-2 + 3, 1)
          # result.equal(2.2 + 4.1, 6.3)
          # result.equal(10 + 2, 12)
          # result.equal('foo' + 'bar', 'foobar')

      #  Shortcut notation that uses single values for single argument parametrization
      #  Assigns 1, 2, 3, 4 to `value` for each generated test case
      #  Verbose notation would be `parameters=((2,), (4,), (6,), (8,))` which
      #  is not that readable.
      @testcase(parameters=(2, 4, 6, 8))
      def is_even(self, env, result, value):
          result.equal(value % 2, 0)


.. _parametrization_combinatorial:

Combinatorial Parametrization
+++++++++++++++++++++++++++++

If you pass a dictionary of lists/tuples as ``parameters`` value, ``@testcase``
decorator will then generate new test methods using a cartesian product of all
of the values from each element. This can be useful if you would like to run a
test using a combination of all possible values.

The example below will generate 27 (3 x 3 x 3) test case methods for each possible
combination of the values from each dict item.

.. code-block:: python

    @testsuite
    class SampleTest(object):

      @testcase(parameters={
          'first_name': ['Ben', 'Michael', 'John'],
          'middle_name': ['Richard', 'P.', None],
          'last_name': ['Brown', 'van der Heide', "O'Connell"]
      })
      def form_validation(self, env, result, first_name, middle_name, last_name):
          """Test if form validation accepts a variety of inputs"""
          form = NameForm()
          form.validate(first_name, middle_name, last_name)

          # The call order for the generated methods will be:
          # form.validate('Ben', 'Richard', 'Brown')
          # form.validate('Ben', 'Richard', 'van der Heide')
          # form.validate('Ben', 'Richard', "O'Connell")
          # form.validate('Ben', 'P.', 'Brown')
          # ...
          # ...
          # form.validate('John', None, 'van der Heide')
          # form.validate('John', None, "O'Connell")

This is equivalent to declaring each method call explicitly:

.. code-block:: python

    @testsuite
    class SampleTest(object):

      @testcase(parameters=(
          ('Ben', 'Richard', 'Brown'),
          ('Ben', 'Richard', 'van der Heide'),
          ('Ben', 'Richard', "O'Connell"),
          ('Ben', 'P.', "Brown"),
          ...
      ))
      def form_validation(self, env, result, first_name, middle_name, last_name):
          """Test if form validation accepts a variety of inputs"""
          ...


See the :ref:`addition_associativity <example_multitest_parametrization>` test
in the downloadable example.

If a ``pre_testcase`` or ``post_testcase`` method is defined in test suite and
used along with parameterized testcases, then it can have an extra argument
named ``kwargs`` to access the parameters of the associated testcase, for non
parameterized testcases an empty dictionary is passed for ``kwargs``.

.. code-block:: python

    @testcase(parameters=(("foo", "bar"), ("baz", "quz")))
    def sample_test(self, env, result, x, y):
        pass

    def pre_testcase(name, self, env, result, kwargs):
        result.log("Param 1 is {}".format(kwargs.get("x")))
        result.log("Param 2 is {}".format(kwargs.get("y")))
        ...

    def post_testcase(name, self, env, result, kwargs):
        ...

.. _parametrization_default_values:

Default Values
++++++++++++++

You can provide partial parametrization context assuming that the decorated
method has default values assigned to the parametrized arguments:

.. code-block:: python

    @testsuite
    class SampleTest(object):

        @testcase(parameters=(
            (5,),  # b=5, expected=10
            (3, 7)  # expected=10
            {'a': 10, 'expected': 15},  # b=5
        ))
        def addition(self, env, result, a, b=5, expected=10):
            result.equal(expected, a + b)


.. _parametrization_custom_name_func:

Testcase name generation
++++++++++++++++++++++++

When you use parametrization, Testplan will try creating a sensible name for each
generated testcase. By default the naming convention is:
``'ORIGINAL_TESTCASE_NAME <arg1=value1, arg2=value2, ... argN=valueN>'``

In the example below, 2 new testcases will be generated, and their names become
``'Add List <number_list=[1, 2, 3], expected=6>'``
and ``'Add List <number_list=[6, 7, 8, 9], expected=30>'``.

.. code-block:: python

    @testsuite
    class SampleTest(object):

        @testcase(
            name="Add List",
            parameters=(
                ([1, 2, 3], 6),
                (range(6, 10), 30),
            )
        )
        def add_list(self, env, result, number_list, expected):
            result.equal(expected, sum(number_list))

User can provide custom name generation functions to override this default behavior
via ``@testcase(name_func=...)`` syntax. You need to implement a function that accepts
``func_name`` and ``kwargs`` as arguments, ``func_name`` being a string and
``kwargs`` being an ``OrderedDict``. See
:py:func:`default_name_func <testplan.testing.multitest.parametrization.default_name_func>`
for sample implementation.

.. code-block:: python

    def custom_name_func(func_name, kwargs):
        return '{func_name} -- (numbers: [{joined_list}], result: {expected})'.format(
            func_name=func_name,
            joined_list=' '.join(map(str, kwargs['number_list'])),
            expected=kwargs['expected']
        )

    @testsuite
    class SampleTest(object):

        @testcase(
            name="Add List",
            parameters=(
                ([1, 2, 3], 6),
                (range(6, 10), 30),
            ),
            name_func=custom_name_func
        )
        def add_list(self, env, result, number_list, expected):
            ...

In the above example, the custom testcase names should be
``'"Add List -- (numbers: [1 2 3], result: 6)"'`` and
``'"Add List -- (numbers: [6 7 8 9], result: 30)"'``. If you deliberately set
``name_func`` to ``None``, then the display names generated are simply
``'Add List 0'`` and ``'Add List 1'``, that is, integer suffixes appended to
the original testcase names, without any argument showed.

.. _parametrization_docstring_func:

Testcase docstring generation
+++++++++++++++++++++++++++++

Similar to testcase name generation, you can also build custom docstrings for
generated testcases via ``@testcase(parameters=...,
docstring_func=custom_docstring_func)`` syntax.

Testplan will then use these docstrings as test descriptions while generating
the test reports.

The ``custom_docstring_func`` function should accept ``docstring`` and
``kwargs`` arguments, ``docstring`` being a  ``string`` or ``None`` and
``kwargs`` being an ``OrderedDict``.

.. code-block:: python

    import os

    def custom_docstring_func(docstring, kwargs):
      """
      Returns original docstring (if available) and
      parametrization arguments in the format ``key: value``.
      """
      kwargs_items = [
          '{}: {}'.format(arg_name, arg_value)
          for arg_name, arg_value in kwargs.items()
      ]

      kwargs_string = os.linesep.join(kwargs_items)

      if docstring:
          return '{}{}{}'.format(docstring, os.linesep, kwargs_string)
      return kwargs_string

    @testsuite
    class SampleTest(object):

        @testcase(
            parameters=(
                ([1, 2, 3], 6),
                (range(6, 10), 30),
            ),
            docstring_func=custom_docstring_func
        )
        def add_list(self, env, result, number_list, expected):
            ...

.. _parametrization_tagging:

Tagging Generated Test Cases
++++++++++++++++++++++++++++

You can tag generated testcases, all you need to do is to pass ``tags`` argument
along with ``parameters``:

.. code-block:: python

  @testsuite
  class SampleTest(object):

      @testcase(
          tags=('tagA', 'tagB'),
          parameters=(
              (1, 2),
              (3, 4),
          )
      )
      def addition(self, env, result, a, b):
          ...

.. _parametrization_tag_func:

It is also possible to use parametrization values to assign tags dynamically,
via ``tag_func`` argument. The ``tag_func`` should accept a single argument
(``kwargs``) which will be the parametrized keyword argument dictionary for that
particular generated testcase.

.. code-block:: python

    def custom_tag_func(kwargs):
        """
        Returns a dictionary that is interpreted as named tag context.
        A string or list of strings will be interpreted as simple tags.
        """
        region_map = {
          'EU': 'Europe',
          'AS': 'Asia',
          'US': 'United States'
        }

        return {
          'product': kwargs['product'].title(),
          'region': region_map.get(kwargs['region'], 'Other')
        }

    @testsuite
    class SampleTest(object):

        @testcase(
            parameters=(
                ('productA', 'US'),  # tags: product=ProductA, region=United States
                ('productA', 'EU'),  # tags: product=ProductA, region=Europe
                ('productB', 'EMEA'),  # tags: product=ProductB, region=Other
                ('productC', 'BR')  # tags: product=ProductC, region=Other
            ),
            tag_func=custom_tag_func
        )
        def product(self, env, result, product, region):
            ...

.. note::

  If you use ``tag_func`` along with ``tags`` argument, testplan will merge the
  dynamically generated tag context with the explicitly passed tag values.


.. _parametrization_decorating:

Decorating Parametrized Testcases
+++++++++++++++++++++++++++++++++

Decorating parametrized testcases uses a different syntax than usual python
decorator convention: You need to pass your decorators via ``custom_wrappers``
argument instead of decorating the testcase via ``@decorator`` syntax. If you
implement custom decorators, please make sure you use
:py:func:`testplan.common.utils.callable.wraps`, instead of ``@functools.wraps``.

.. code-block:: python

    from testplan.common.utils.callable import wraps

    def my_custom_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ...

    @testsuite
    class SampleTest(object):

        # Decorating a normal testcase, can use `@decorator` syntax.
        @my_custom_decorator
        @testcase
        def normal_test(self, env, result):
            ...

        # For parametrized testcases, need to use `custom_wrappers` argument.
        @testcase(
            parameters=(
                (1, 2),
                (3, 4),
            ),
            custom_wrappers=my_custom_decorator  # can pass a single decorator
                                                 # instead of a list with
                                                 # single element
        )
        def addition(self, env, result, a, b):
            ...

.. _testcase_parallelization:

Testcase Parallel Execution
---------------------------

It is possible to run testcases in parallel with a thread pool. This feature
can be used to accelerate a group of testcases that spend a lot of time on IO
or waiting. Due to Python global interpreter lock, the feature is not going to
help CPU-bounded tasks, it also requires testcase written in a thread-safe way.

To enable this feature, instantiate MultiTest with a non-zero ``thread_pool_size``
and define ``execution_group`` for testcases you would like to run in parallel.
Testcases in the same group will be executed concurrently.

.. code-block:: python

    @testsuite
    class SampleTest(object):

        @testcase(execution_group='first')
        def test_g1_1(kwargs):
            ...

        @testcase(execution_group='second')
        def test_g2_1(kwargs):
            ...

        @testcase(execution_group='first')
        def test_g1_2(kwargs):
            ...

        @testcase(execution_group='second')
        def test_g2_2(kwargs):
            ...

        my_multitest = MultiTest((name='Testcase Parallezation',
                                  suites=[SampleTest()],
                                  thread_pool_size=2))

.. _testcase_timeout:

Testcase timeout
----------------

If testcases are susceptible to hanging, or not expected to be time consuming, you may want to spot this and abort those testcases early. You can achieve it by passing a "timeout" parameter to the testcase decorator, like:

.. code-block:: python

    @testcase(timeout=10*60)  # 10 minutes timeout, given in seconds.
    def test_hanging(self, env, result):
        ...

If the testcase times out it will raise a :py:class:`TimeoutException <testplan.common.utils.timing.TimeoutException>`, causing its status to be "ERROR". The timeout will be noted on the report in the same way as any other unhandled Exception. The timeout parameter can be combined with other testcase parameters (e.g. used with parametrized testcases) in the way you would expect - each individual parametrized testcase will be subject to a seperate timeout.

Also keep in mind that testplan will take a little bit of effort to monitor execution time of testcases with ``timeout`` attribute, so it is better to allocate a little more seconds than you have estimated how long a testcase would need.

Similarly, ``setup`` and ``teardown`` methods in a test suite can be limited to run in specified time period, like this:

.. code-block:: python

    from testplan.testing.multitest.suite import timeout

.. code-block:: python

    @timeout(120)  # 2 minutes timeout, given in seconds.
    def setup(self, env, result):
        ...

    @timeout(60)  # 1 minute timeout, given in seconds.
    def teardown(self, env):
        ...

It's useful when ``setup`` has much initialization work that takes long, e.g. connects to a server but has no response and makes program hanging. Note that this ``@timeout`` decorator can also be used for ``pre_testcase`` and ``post_testcase``, but that is not suggested because pre/post testcase methods are called everytime before/after each testcase runs, they should be written as simple as possible.

Hooks
-----

  In addition suites can have ``setup`` and ``teardown`` methods. The ``setup``
  method will be executed on suite entry, prior to any testcase if present.
  The ``teardown`` method will be executed on suite exit, after setup and all
  ``@testcase``-decorated testcases have executed.

  Again, the signature of those methods is checked at import time, and must be
  as follows:

  .. code-block:: python

    def setup(self, env):
        ...

    def teardown(self, env):
        ...

  The result object can be optionally used to perform logging and basic
  assertions:

  .. code-block:: python

    def setup(self, env, result):
        ...

    def teardown(self, env, result):
        ...

  To signal that either ``setup`` or ``teardown`` hasn't completed correctly,
  you must raise an exception. Raising an exception in ``setup`` will abort
  the execution of the testsuite, raising one in ``teardown`` will be logged
  in the report but will not prevent the execution of the next testsuite.

  Similarly suites can have ``pre_testcase`` and ``post_testcase`` methods.
  The ``pre_testcase`` method is executed before each testcase runs, and the
  ``post_testcase`` method is executed after each testcase finishes. Exceptions
  raised in these methods will be logged in the report. Note that argument
  ``name`` is populated with name of testcase.

  .. code-block:: python

    def pre_testcase(self, name, env, result):
        pass

    def post_testcase(self, name, env, result):
        pass


.. _Xfail:

Xfail
-----

Testcases and testsuites that you expect to fail can be marked with the `@xfail` decorator. These failures will be visible in the test report, highlighted in orange. Expected failures will not cause the testplan as a whole to be considered a failure.

The Xfail means that you expect a test to fail for some reason. If a testcase/testsuite is unstable (passing sometimes, failling other times) then `strict=False` (default value is `False`) can be used. This means if the testcase/testsuite fails it will be marked "expected to fail" (`xfail`), if it passes it will be marked as "unexpectedly passing" (`xpass`). 
Both `xfail` and `xpass` don't cause the parent testsuite or MultiTest to be marked as a failure.

The ``xfail`` decorator mandates a reason that explains why the test is marked as Xfail:

.. code-block:: python

    @xfail(reason='unstable test')
    def unstable_testcase(self, env, result):
        ...


If a test is expect to fail all the time, you can also use the `strict=True` then `xpass` will be considered as `fail`. This will cause the unexpectedly passing result to fail the testcase or testsuite.

.. code-block:: python

    @xfail(reason='api changes', strict=True)
    def fail_testcase(self, env, result):
        ...

Skip if
-------

  :py:func:`@skip_if <testplan.testing.multitest.suite.skip_if>` decorator can
  be used to annotate a testcase. It take one or more predicates, and if any of
  them evaluated to True, then the testcase will be skipped by MultiTest instead
  of being normally executed. The predicate's signature must name the argument
  ``testsuite`` or a ``MethodSignatureMismatch`` exception will be raised.

  .. code-block:: python

    def skip_func(testsuite):
        # It must accept an argument named "testsuite"
        return True

    @testsuite
    class MySuite(object):

        @skip_if(skip_func, lambda testsuite: False)
        @suite.testcase
        def case(self, env, result):
            pass

Logging
-------

Python standard logging infrastructure can be used for logging, however testplan provide mixins to use a conveniently configured logger from testcases.

See also the :ref:`a downloadable example <example_multitest_logging>`.

:py:class:`LogCaptureMixin <testplan.testing.multitest.logging.LogCaptureMixin>` when inherited provide a ``self.logger`` which will log to the normal testplan log. Furthermore the mixin provide a context manager :py:meth:`capture_log(result) <testplan.testing.multitest.logging.LogCaptureMixin.capture_log>` which can be used to automatically capture logs happening in the context and attaching it to the result.

.. code-block:: python

    @testsuite
    class LoggingSuite(LogCaptureMixin):

        @testcase
        def testsuite_level(self, env, result):
            with self.capture_log(
                result
            ) as logger:  # as convenience the logger is returned but is is really the same as self.logger
                logger.info("Hello")
                self.logger.info("Logged as well")

The code above will capture the two log line and inject it into the result. The capture can be configured to capture log to a file and attach to the result. It also possible to capture the base testplan logger, or even the root logger during the execution of the context. If the default formatting is not good enough it can be changed for the report. For all these options see :py:meth:`LogCaptureMixin.capture_log <testplan.testing.multitest.logging.LogCaptureMixin.capture_log>`

:py:class:`AutoLogCaptureMixin <testplan.testing.multitest.logging.AutoLogCaptureMixin>` when inherited it automatically capture and insert logs to the result for every testcase.

.. code-block:: python

    @testsuite
    class AutoLoggingSuite(AutoLogCaptureMixin):
        """
        AutoLogCaptureMixin will automatically add captured log at the end of all testcase
        """

        @testcase
        def case(self, env, result):
            self.logger.info("Hello")

        @testcase
        def case2(self, env, result):
            self.logger.info("Do it for all the testcases")

The capture can be tweaked to set up ``self.log_capture_config`` during construction time, very similar to the :py:meth:`LogCaptureMixin.capture_log <testplan.testing.multitest.logging.LogCaptureMixin.capture_log>`

.. code-block:: python

    def __init__(self):
        super(AutoLoggingSuiteThatAttach, self).__init__()
        self.log_capture_config.attach_log = True

