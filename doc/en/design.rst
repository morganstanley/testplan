Design doc
==========

Testplan structure is written in a way to promote usage of base classes that
provide common functionality. These base classes may be inherited by more
complex classes which represent objects in diferent areas: tests, drivers,
pools, exporters, etc. Each class accepts configuration and can inherit the
configuration of the base class as well.

Key reasons for using this structure:

  1. Avoid code copy-paste across similar classes.
  2. Provide a way to define relations between classes
     (i.e a Multitest has many drivers, a Testplan has many pools).
  3. Provide a functional .abort() process that takes under consideration the
     hierarchical dependency of objects.
  4. Provide a way to define configuration options for the objects while having
     access to a global configuration.
  5. Ctrl-C and sigterm/sigint handling without hanging.
  6. Common logging and runpath(output files of classes) creation logic.
  7. User programmatic customizations support in various functionality areas.
  8. Parallel and remote execution.
  9. Integration of runtime with other languages or UI tools (i.e Java, React).

Terminology
-----------

Base classes
++++++++++++

Config
``````

:py:class:`~testplan.common.config.base.Config` - configuration objects with
default values or user input with \*\*options after performing a validation stage.
Config objects can inherit other Config objects and alter or define additional
ConfigOption items:

  * Config instances may have container references that are used to retrieve a
    config option value if this is not present in the current config.
    The ``__getattr__`` method in :py:class:`~testplan.common.config.base.Config`
    contains the rules on whether current or container config option will be
    used.

Entity
``````

:py:class:`~testplan.common.entity.base.Entity` is the first and most important
base class to be used by by classes that:

  * accept configuration that inherit :py:class:`~testplan.common.config.base.Config`
  * have a status with capability to validate transitions (i.e it's legal to go
    from STARTING to STARTED but not from STOPPING to STARTED)
  * need to be able to be aborted and a way to be identified as active (not aborted)
  * need a reference to a "parent" entity to inherit configuration (i.e MultiTest
    parent is the TestRunner)
  * make use of temporary directory for output files (runpath)
  * have dependency entities that need to be aborted before existing entity (i.e
    drivers need to be aborted before Multitest and pools need to be aborted
    before TestRunner)

Resource
````````

:py:class:`~testplan.common.entity.base.Resource` subclass of
:py:class:`~testplan.common.entity.base.Entity` class is used to create
temporary helpful resources that simply need to be STARTED and then STOPPED.
They are NOT creating any result at all. I.e drivers are resources of Multitest
and pools are resources TestRunner.

Runnable
````````

:py:class:`~testplan.common.entity.base.Runnable` subclass of
:py:class:`~testplan.common.entity.base.Entity`  are entities that:

  1. Execute a number of steps
  2. Create and provide a RunnableResult that has a "passed" or not state
  3. May be able to be executed in an interactive mode based on their
     interactive_handler interactive_runner.

RunnableManager
```````````````

:py:class:`~testplan.common.entity.base.RunnableManager` objects will execute
a Runnable object in a seperate thread protecting it from abort signals like
SIGINT/TERM.

Report/Group
````````````

:py:class:`~testplan.common.report.base.Report` and
:py:class:`~testplan.common.report.base.ReportGroup` classes are implementing
the base functionality (merge, flatten, indexing) to create more specialized
reports on top of them like
:py:class:`test <testplan.report.testing.base.TestReport>` reports.

Exporter
````````

Exporters inherit :py:class:`~testplan.common.exporters.BaseExporter` are
responsible to export a created report object (i.e json, xml, pdf, webserver).


Main classes
++++++++++++

Testplan
````````

:py:class:`~testplan.base.Testplan` subclass of
:py:class:`~testplan.common.entity.base.RunnableManager` is the main class to be
used as it manages the main :py:class:`~testplan.runnable.base.TestRunner` instance
that is the implementation of the actual testing framework and that it's
configurable with :py:class:`~testplan.runnable.base.TestRunnerConfig` options and
that provides a :py:class:`~testplan.base.TestplanResult` object representing
the result of the runnable steps execution and also contains a report.

.. note::
    A user can instantiate a plan object directly ``plan = Testplan(**options)``
    and then manually use ``plan.run()`` to execute it
    or decorate a main function with ``@test_plan`` decorator and call it.

:py:class:`~testplan.base.Testplan` accepts a ``parser`` object that will parse
**command line options** and use these **ONLY IF** the values are **NOT**
programmatically hardcoded in \*\*options of the constructor. This is due to the
default arguments of the parser object that makes not obvious to identify if
a parser.attribute is user command line input or just a default value. So
**DO NOT** hardcode values in constructors if you want them to be overwritten by
command line arguments OR parser needs to change to wrap the defaul values into
DefaultValue() objects similar to :py:class:`~testplan.common.config.base.Config`
implementation approach.

After subclassing the base :py:class:`~testplan.common.entity.base.Resource`
and :py:class:`~testplan.common.entity.base.Runnable` classes we can compose
more meaningful classes that compose the actual testing framework components.
So as the following image displays:

  * Testplan has the actual TestRunner testing framework inside it and the
    framework itself is a runnable that executes steps (i.e start/stop pools,
    invoke test result exporters etc).
  * TestRunner framework has Resources that can be started/stopped that may be
    local test runners, pools to execute tasks (callable that return actual tests)
    or the environments container resources to maintain environments of drivers
    outside of tests. (This is useful also when interacting from other languages
    that only need to make use of the environment capability of Testplan.)

.. image:: ../images/design/testplan.png

MultiTest
`````````

:py:class:`~testplan.testing.multitest.base.MultiTest` is the native python
testing framework supported by Testplan which is a runnable class that executes
steps (i.e start/drivers drivers, execute python testcases) and creates a
MultitestResult that contains a report. The environment is a collection of
drivers that will be accessed from within the testcases.

.. image:: ../images/design/multitest.png

Driver
``````

:py:class:`~testplan.testing.multitest.driver.base.Driver` base class provide
common functionality to usual drivers like extracting values from logs and
expose attributes via context mechanism so that they can be retrieved at runtime
by other drivers. Also they provide **virtual** functions like
pre/post_start/stop to be able to be customized by users when implementing a
custom behaviour.

Task
````

:py:class:`~testplan.runners.pools.tasks.base.Task` containers are holding the
information for later initialization of actual tests and can be serialized
and dispatched in external python interpreters for the execution.

Pool
````

:py:class:`~testplan.runners.pools.base.Pool` objects are Executor resources of
Tasks and based on their implementation they execute tests differently.
I.e :py:class:`~testplan.runners.pools.process.ProcessPool` executes tests in
external process workers in the same host while
:py:class:`~testplan.runners.pools.remote.RemotePool` executes tests in
remote interpreters in different hosts.

TestReport
``````````

:py:class:`~testplan.report.testing.base.TestReport` (top level Testplan report)
and :py:class:`~testplan.report.testing.base.TestGroupReport` (Multitest,
testsuite, etc..) objects are containing all result information of the tests and
status. They can be serialized and deserialized and this is a requirement as
they are a part of the result objects of runnables that are transferred between
different interpreters in process and remote pools.


Repo structure
--------------

Code
++++

**testplan/common** directory contains common base classes and utilities that
may be used by multiple modules in the repository. Code under this directory
need to be generic enough and must not have any dependency on testplan code
outside *tesptlan/common* directory structure.

**testplan/exporters** directory contains actual implementation of exporters of
reports including test reports to json, xml, pdf, ui formats.

**testplan/report** directory contains actual implementation of reports
including test reports that can be later used by test exporters.

**testplan/runnable** directory contains the main runnable testing framework
functionality including interactive mode.

**testplan/runners** directory contains the test runner and task execution pools
(i.e thread, process, remote) and task and task results definition.

**testplan/testing** directory contains the test runnables inluding MultiTest
that execute testsuites and testcases and produce a test report. It also
includes features for tagging, ordering, listing the cases but not all tests
may support them. The base class of all tests is
:py:class:`~testplan.testing.base.Test` that provides an environment of drivers
and the base class for tests that will execute a binary to run the actual
testcases is :py:class:`~testplan.testing.base.ProcessRunnerTest`.

**testplan/base.py** module contains the main
:py:class:`~testplan.base.Testplan` and @test_plan definitions.

Tests
+++++

**tests/functional** directory contains all functional tests organised in a
directory structure mirroring testplan code structure.

    * *test/functional/examples* contains the tests of the downloadable examples.

**tests/unit** directory contains all unit tests organised in a directory
structure mirroring testplan code structure.

Docs
++++

**doc/en** directory contains all .rst files documenting all logical components.

**doc/en/api** directory contains the .rst files for automatic API documentation
generation from source code.

Examples
++++++++

**examples** directory contains premade examples demonstrating common use cases
making user adaptation easier. A downloadable example need to have its
corresponding documentation entry in **doc/en/download** directory so that
the users can access it from the documentation webpage.

Execution modes
+++++++++++++++

  * **Local** execution is the default. There are two options:

      1. :py:meth:`plan.add() <testplan.runnable.base.TestRunner.add>`
         that will add a test in the local runner that executes
         tests sequentially in a local thread.
      2. :py:meth:`plan.schedule() <testplan.runnable.base.TestRunner.schedule>`
         that will schedule a task in a pool that can be a
         local thread pool or process pool.

    When adding or scheduling a Test (i.e MultiTest) it is being added/scheduled
    as a whole in a single executor and it's down to its internal implementation
    of how the testsuites/testcases will be executed.

  * **Execution groups** can be used in MultiTest testcases so they can run in
    parallel in groups against the same live environment. Documented
    :ref:`here <testcase_parallelization>`.

  * :ref:`Pools <Pools>` are implementing specific execution strategy and can
    be combined in the same Testplan making it possible for tests to be executed
    in different threads/processes/hosts or a specific cloud platform.
    **Remote** execution can be achieved using :ref:`RemotePool <RemotePool>`
    as documented.

Interactive mode
----------------

By default, testplan will operate in a "batch" mode - it will run all tests
in a pre-defined order (either sequentially or parallelised by some execution
pool), produce a hierarchical report tree containing the test results, and then
run exporters to convert the report tree into various output forms (JSON, PDF,
web UI etc.). Once started to run in batch mode, Testplan needs no further
input and will run to completion unless interrupted by some signal.

The interactive mode on the other hand allows tests to be run on-demand, with
the results immediately displayed as they are available. Interactive mode
is useful for local development - it provides a graphical interface for
choosing which testcases to run and allows testcases to be modified and re-run
iteratively without having to restart a testing environment.

The main technical challenge introduced by the interactive mode is having to
manage updating a mutable report tree as testcases are run in a consistent and
thread-safe manner.

When testplan is running interactively, it can be thought of as separated into
two main software layers:

  1. The back-end: a multi-threaded python process, running an HTTP server
     which presents a REST API for reading and updating the report state.

  2. The front-end: a web app running in the browser, powered by React JS.
     In most cases, only one client is expected to connect to the back-end at a
     time - however, the interactive mode has been architected to allow multiple
     clients to connect without conflicting.

REST is a very popular API architecture used widely in modern web services.
REST means "REpresentational State Transfer" - which, in short, means it is all
about managing the transfer of **state** and not **actions**. Typically,
actions will be triggered as side-effects of state updates. It is very
useful to focus on the management of mutable state when dealing with
applications running in more than one location. For more information on REST,
I recommend reading this article:
https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api

The Golden Rule underlying the design of the interactive mode is that
**the back-end is the sole owner of the report state**. The front-end will
read the report state by making HTTP GET requests, storing a copy locally,
and it will **request** to update the report state on the backend by making
HTTP PUT requests. However, it is at the discretion of the back-end to accept
or deny update requests. This means the back-end is the sole decider of what
happens if the front-end mistakenly sends multiple conflicting updates, or if
multiple clients are connected to the same back-end at once. As a
corollary of this Golden Rule, the front-end should not update its own copy
of the report state unless told to do so by the back-end, through the content
of a GET or PUT response.

Interactive back-end design
+++++++++++++++++++++++++++

In python-land, the interactive mode is implemented through a few key classes:

  1. :py:class:`~testplan.interactive.base.TestRunnerIHandler` is the overall
     manager when running interactively. It owns the report tree, which is
     initialised to an empty skeleton containing testcases but no results.
     The :py:class:`~testplan.interactive.base.TestRunnerIHandler` handles
     running individual testcases and merges their results into its report
     tree when they complete. It owns a thread pool to allow multiple tests
     to be run (or queued for running) asynchonously. To be thread-safe, a
     report_mutex is provided by this class which **must** be held when
     either reading or mutating any part of the report tree.

  2. :py:class:`~testplan.interactive.http.TestRunnerHTTPHandler` defines the
     REST API and owns an HTTP server which is used to serve the API as well
     as the static HTML/JS/CSS etc. files required for the front-end web app.
     The :py:class:`~testplan.interactive.http.TestRunnerHTTPHandler` will
     call methods on its owning
     :py:class:`~testplan.interactive.base.TestRunnerIHandler` instance when
     required to perform actions such as running tests or starting test
     resources, as a side-effect from accepting certain state update requests
     (e.g. when updating the status of a testcase to RUNNING, it will trigger
     that testcase to actually run). It handles all validation of update
     requests.

  3. :py:class:`~testplan.testing.base.Test` is the base class all Tests
     inherit from, and defines abstract methods required for a Test sub-class
     to be compatible with the interactive mode. Unlike batch mode, where a
     Test runner will run a pre-defined list of testcases and return a single
     report sub-tree, for interactive mode a Test runner needs to run
     testcases iteratively. As mentioned above, the
     :py:class:`~testplan.interactive.base.TestRunnerIHandler` instance
     owns the main report tree, so individual Test runners should not directly
     mutate any part of the report tree - instead, they should yield individual
     testcase reports as the testcases are run, and let the
     :py:class:`~testplan.interactive.base.TestRunnerIHandler` handle merging
     those testcase reports into the main report tree. Currently
     :py:class:`~testplan.testing.multitest.MultiTest` is the only Test
     sub-class which correctly implements all methods required to run
     interactively.

Each of the classes above has unit-tests to cover their respective
functionalities in isolation. In addition, there is a functional test
(**tests/functional/testplan/runnable/interactive/test_api.py**)
which spins up an interactive testplan with real testcases and tests running
tests and reading their results by sending HTTP requests into the REST API.

Interactive front-end design
++++++++++++++++++++++++++++

The front-end is actually the exact same web-app used to render test results
from the batch mode. The single web-app uses
`react-router <https://reacttraining.com/react-router/web/guides/quick-start>`_
to distinguish between the URLs used for batch or interactive modes and
tweak its behaviour in each case. It would have been possible to create a
completely separate package for the interactive web-app and extract the
common code into a library, however this would significantly increase the
complexity of developing and building both UIs so this hybrid approach was
chosen instead.

All web-app code can be found under **testplan/web_ui/testing/src**. The key
component for interactive mode is the ``InteractiveReport`` component. It owns
a copy of the report tree (though as noted above, ultimately the back-end
is the master of the report tree), and handles the necessary API requests to
keep the report state in sync and make API update requests to trigger tests to
run, test environments to start/stop etc.

Currently, the front-end uses a simple short-polling method to keep its report
state in sync with the back-end. Every second, it polls the back-end for
changes. Since refreshing the report state entirely every second would quickly
become untenable as the report grows in size, the back-end does not return
the entire report (sub-)tree for each endpoint but rather a "shallow" copy.
A shallow copy includes all data associated with that node in the tree, but
instead of directly embedding its child entries, only the UIDs of each child
is included. That way, multiple API requests are required to query the entire
report tree. Further, each node in the report tree has a hash value which can
be used to check if it or any of its children have been modified. Therefore,
the report tree is updated recursively with the hash value used to
short-circuit when there are no modifications down a given branch.

There are many alternative strategies which could have been used to keep the
report in sync with the backend. Websockets, Server Sent Events (SSEs) or
HTTP long-polling could allow the backend to notify the front-end when some
part of the report tree is updated. These techniques would allow the UI to
update more quicker and in a more efficient manner than simple short-polling
allows, however they would add complexity and need to be carefully designed
to not allow the front-end state to become unsynchronised, or allow
either back- or front-end to be overwhelmed with pushing notifications when
many updates are available at once. Right now, the responsiveness of the
UI using simple short-polling is not amazing but (to my mind) "good enough".
We may want to revisit this area when dealing with larger reports or when we
wish to polish the UI to be more than simply "good enough".

The navigation-related UI components are significantly modified for use in the
interactive mode, in order to accomodate the extra buttons to trigger tests to
run or to toggle the state of test environments. The modified components can
be found by searching for names beginning with ``InteractiveNav``.


User Interface
--------------

The UI code was written using React (JSX), it is highly recommended to first
read through the
`React documentation <https://reactjs.org/docs/hello-world.html>`_, in
particular the main concepts.

Components
++++++++++

Each React component should have its own file. This file should contain
everything the component uses to render the final HTML (JSX code + CSS). We have
used `Aphrodite <https://github.com/Khan/aphrodite>`_ to keep the CSS
inside the JS file. This improves readability, everything you need to know about
a single component is in the one file (save for common utilities or defaults).
Each component should be as general as possible to allow it to be reused. We
should also strive for simple and small components to enhance readability.

Each component should define its
`PropTypes <https://reactjs.org/docs/typechecking-with-proptypes.html>`_.
This allows us to typecheck whilst developing & testing, it won't cause issues
in production. This could be extended in future to also work for state.

Utilities & defaults
++++++++++++++++++++

Some common functions have been written in utility files. These are pure
JavaScript functions that don't rely on React. Moving them to a separate file
improves readability in the component files and allows them to be more easily
reused.

The components and utility functions shouldn't have hardcoded values, these
should be placed in the common defaults file and imported when needed.

Documentation
+++++++++++++

Currently the UI code has docstrings on every:

  * React component
  * Prop type for a component
  * Non React function within a component
  * Utility function

Each docstring has a description, list of parameters, the return of the function
and whether the object is public or private. The docstrings should ideally be
updated when the code is changed.

Style
+++++

It doesn't matter which style we use, as long as we are consistent with it. When
writing JSX code refer to the
`React documentation <https://reactjs.org/docs/hello-world.html>`_ to check
what style to use. The pure JavaScript code is very similar. We use ESLint to
check the code when it is built.

For the directory structure, again only consistency matters:

  * Directories are written in upper camel case (e.g. AssertionPane).
  * Utility files are written in lower camel case (e.g. basicAssertionUtils.js).
  * Component files are written in upper camel case (e.g. BasicAssertion.js).

Tests
+++++

Each component should have a corresponding test file under a ``__tests__``
directory. We are using enzyme and jest for testing. Enzyme allows us to shallow
mount the components, better for unit testing. Jest is a good framework for
unit testing JavaScript code. Try not to have more than one snapshot test per
component. The snapshot tests are used to quickly check the general HTML layout
of the component is correct. We can then alter the props and check specific
components have changed with other tests. This keeps the tests more readable,
you can see what is meant to have changed easier when reading the tests.
Currently only unit test in future we may want to do functional tests etc.
