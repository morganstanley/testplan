.. _Pools:

Pools
=====

Pools are Test :py:class:`executors <testplan.runners.base.Executor>`
that instantiate an array of
:py:class:`workers <testplan.runners.pools.base.Worker>` that pull and
execute them in parallel. Test instances are generally not serializable so
:py:class:`~testplan.runners.pools.tasks.base.Task` s are being *scheduled* to
the pools instead.

.. image:: ../gif/worker_pool/worker_pool.gif

Pools are resources that can be added in a plan using
:py:meth:`~testplan.runnable.base.TestRunner.add_resource` method of the
:py:class:`plan <testplan.base.Testplan>` object.

.. code-block:: python

    @test_plan(name='PoolDemo')
    def main(plan):
        ...
        pool = Pool(**options)
        plan.add_resource(pool)
        ...

Task / Result
-------------

Task
++++

A Task is an object that holds the path to a target that can be materialized
at runtime and executed by worker instances. For example, if a target function
that creates a MultiTest is in file ``./tasks.py``:

.. code-block:: python

    # ./tasks.py

    def make_multitest():
        test = MultiTest(name='TestName',
                         suites=[Testsuite1(), Testsuite2()],
                         environment=[Server(name='server'), ...])
        return test

the task that holds the information to materialize the MultiTest at runtime
is the following:

.. code-block:: python

    # ./test_plan.py

    task = Task(target='make_multitest',
                module='tasks',
                path=os.path.dirname(os.path.abspath(__file__)))  # same dir

The target function can accept arguments:

.. code-block:: python

    # ./tasks.py

    def make_multitest(index):
        test = MultiTest(name='Test_{}'.format(index),
                         ...)
        return test

and many Test instances can be created from the same target function:

.. code-block:: python

    # ./test_plan.py

    for idx in range(10):
        task = Task(target='make_multitest',
                    module='tasks',
                    path=os.path.dirname(os.path.abspath(__file__)),
                    args=(idx,))  # or kwargs={'index': idx}

With argument `rerun` testplan can rerun the task up to user specified times
until it passes:

.. code-block:: python

    # ./test_plan.py

    task = Task(target='make_multitest',
                module='tasks',
                path=os.path.dirname(os.path.abspath(__file__)),
                rerun=3)  # default value 0 means no rerun

Task rerun can be disabled at pool level with ``allow_task_rerun`` parameter.

.. code-block:: python

    # ./test_plan.py

    pool = ThreadPool(name="MyPool", allow_task_rerun=False)

Task can associate with a `weight` value, and it affects task scheduling - the
larger the weight, the sooner task will be assigned to a worker. Default weight
is 0, and tasks with the same weight will be scheduled in the order they are added.

.. code-block:: python

    # ./test_plan.py

    task = Task(target='make_multitest',
                module='tasks',
                path=os.path.dirname(os.path.abspath(__file__)),
                weight=100)


TaskResult
++++++++++

A :py:class:`~testplan.runners.pools.tasks.base.TaskResult` is the object that
is returned to the pool by the worker and contains either the actual result,
or the error that prevented the execution.

plan.schedule
-------------

:py:meth:`plan.schedule <testplan.runnable.base.TestRunner.schedule>` is used to
schedule a
Task to a Pool and once it's scheduled and pool is started, it will be pulled
and executed by a worker.

.. code-block:: python

        # add a pool to the plan
        pool = Pool(name='PoolName', ...)
        plan.add_resource(pool)

        # schedule a task to the pool
        task = Task(target='make_multitest', ...)
        plan.schedule(task, resource='PoolName')

Basic pool types
----------------

The base pool object accepts some
:py:class:`configuration <testplan.runners.pools.base.PoolConfig>` options that
may be vary based on pool implementations.

These are the current built-in pool types that can be added to a plan:

  1. :ref:`Thread pool <ThreadPool>`
  2. :ref:`Process pool <ProcessPool>`
  3. :ref:`Remote pool <RemotePool>`


.. _ThreadPool:

ThreadPool
++++++++++

In a thread pool,
:py:class:`workers <testplan.runners.pools.base.Worker>` are started in separate
threads and they pull tasks from the pool using a transport layer that lives in
the same memory space. The workers are materializing the actual Tests, execute
them and send :py:class:`results <testplan.runners.pools.tasks.base.TaskResult>`
back to the main pool.

.. code-block:: python

    from testplan.runners.pools import ThreadPool

    @test_plan(name='ThreadPoolPlan')
    def main(plan):
        # Add a thread pool of 4 workers.
        pool = ThreadPool(name='MyPool', size=4)
        plan.add_resource(pool)

        # Schedule 10 tasks to the thread pool to execute them 4 in parallel.
        for idx in range(10):
            task = Task(target='make_multitest',
                        module='tasks')
            plan.schedule(task, resource='MyPool')

See a downloadable example of a :ref:`thread pool <example_pool_thread>`.

.. _ProcessPool:

ProcessPool
+++++++++++

Similar to the :ref:`thread pool <ThreadPool>`, the worker interpreters are
started in separate processes and communicate with the pool via
:py:class:`ZMQ transport <testplan.runners.pools.child.ZMQTransport>` with TCP
connection using ``localhost``. During this communication process, the Tasks
and TaskResults are being serialized and de-serialized so all they input
arguments need to support that as well.

.. code-block:: python

    from testplan.runners.pools.process import ProcessPool

    @test_plan(name='ProcessPoolPlan')
    def main(plan):
        # A pool with 4 child process workers.
        pool = ProcessPool(name='MyPool', size=4)
        plan.add_resource(pool)

        # Schedule 10 tasks to the process pool to execute them 4 in parallel.
        for idx in range(10):
            # All Task arguments need to be serializable.
            task = Task(target='make_multitest',
                        module='tasks',
                        path='.')
            plan.schedule(task, resource='MyPool')

See a downloadable example of a :ref:`process pool <example_pool_process>`.

.. _RemotePool:

RemotePool
++++++++++

Remote pool is using ssh to start remote worker interpreters that are
communicating with the local pool with the
:py:class:`ZMQ <testplan.runners.pools.child.ZMQTransport>` transport as well.
During this process, the local workspace will be transferred to the remote
workers (if needed) and the workers will start local 'thread' or 'process'
pools, based on their configuration.

.. code-block:: python

    from testplan.runners.pools.remote import RemotePool

    @test_plan(name='RemotePoolPlan')
    def main(plan):
        # A pool with 2 remote workers.
        # One with 2 local workers and the other with 1.
        pool = RemotePool(name='MyPool',
                          hosts={'hostname1': 2,
                                 'hostname2': 1})
        plan.add_resource(pool)

        # Schedule 10 tasks to the remote pool to execute them 3 in parallel.
        for idx in range(10):
            # All Task arguments need to be serializable.
            task = Task(target='make_multitest',
                        module='tasks',
                        path='.')
            plan.schedule(task, resource='MyPool')

See a downloadable example of a :ref:`remote pool <example_pool_remote>`.

Fault tolerance
---------------

There are some mechanisms enabled to prevent failures of Tests due to system
failures and their behaviour is a part of
:py:class:`pool configuration <testplan.runners.pools.base.PoolConfig>`:

    1. **Worker not responsive**: Workers (excluding Thread workers) are sending
       heartbeat messages back to the pool and the frequency can be set using
       ``worker_heartbeat`` option.
       If worker fails to send a number of heartbeats (``heartbeats_miss_limit``
       option), all tasks assigned to the worker will be reassigned to the pool.
    2. **Task retry**: If a worker dies while running a task, testplan will
       restart the worker and retry the task (for 2 times max). Note that this
       retry behavior doesn't have to do with the Task's rerun setting.

.. _Multitest_parts_scheduling:

MultiTest parts scheduling
--------------------------

A Task that returns a MultiTest can be scheduled in parts in one or more pools.
Each MultiTest will have its own environment and will run a subtotal of testcases
based on which part of the total number of parts it is. So each MultiTest part will
produce its own report entry, these entries can be merged before exported.

To split a MultiTest task into several parts, we can provide a tuple of 2 elements
as a parameter, the first element indicates the sequence number of part, and the
second one is the number of parts in total. For the tuple (M, N), make sure that
N > 1 and 0 <= M < N, where M and N are both integers.

.. code-block:: python

    from testplan.runners.pools import ThreadPool

    @test_plan(name='ThreadPoolPlan', merge_scheduled_parts=False)
    def main(plan):
        # Add a thread pool of 3 workers.
        # Also you can use process pool or remote pool instead.
        pool = ThreadPool(name='MyPool', size=3)
        plan.add_resource(pool)

        # Schedule 10 tasks to the thread pool.
        # A parameter `part_tuple` is provided to indicate which part it is.
        for idx in range(10):
            task = Task(target='make_multitest',
                        module='tasks',
                        kwargs={'part_tuple': (i, 10)})
            plan.schedule(task, resource='MyPool')

If you set merge_scheduled_parts=True, please be sure that all parts of a MultiTest
will be executed, for example, if a MultiTest is split into 3 parts, then 3 tasks
containing MultiTest part should be scheduled, with the parameter tuple (0, 3),
(1, 3) and (2, 3) for each task, also note that a MultiTest can only be schedule
once, or there will be error during merging reports.

See a downloadable example of :ref:`MultiTest parts scheduling <example_multiTest_parts>`.

.. _task_discover:

Task discover
-------------

For some projects, user may find task target definition (e.g the make_multitest
function) and ``plan.schedule`` call become rather repetitive. To reduce boilerplate
code, :py:meth:`@task_target <testplan.runners.pools.tasks.base.task_target>` and
:py:meth:`plan.schedule_all <testplan.runnable.base.schedule_all>` are introduced
to do task discovery.

.. code-block:: python

    plan.schedule_all(
        path=".",
        name_pattern=r".*tasks\.py$",
        resource="MyPool",
    )

In the code above, testplan will go look for @task_target decorated functions
in modules that matches the ``name_pattern`` under current working directory.

.. code-block:: python

    @task_target
    def make_multitest():
        # A test target shall only return 1 runnable object
        test = MultiTest(name="MTest", suites=[Suite()])
        return test

Once found, task object will be created from the target, and scheduled to pool.
It is possible to create multiple task objects out of one target with
`parameters` specified:

.. code-block:: python

    @task_target(
        parameters=(
            # positional args to be passed to target, as a tuple or list
            ("MTest1", None, [SimpleSuite1, SimpleSuite2]),
            # keyword args to be passed to target, as a dict
            dict(
                name="MTest2-1",
                part_tuple=(0, 2),
                suites=[ComplicatedSuite],
            ),
            dict(
                name="MTest2-2",
                part_tuple=(1, 2),
                suites=[ComplicatedSuite],
            ),
        ),
        # additional arguments of Task class
        rerun=1,
        weight=1,
    )
    def make_multitest(name, part_tuple=None, suites=None):
        # A test target shall only return 1 runnable object
        test = MultiTest(
            name=name, suites=[cls() for cls in suites], part=part_tuple
        )
        return test

The code above specifies a collections of parameters in `@task_target`, and each
entry will be used create one task - thus 3 tasks will be created from the target.

For a complete and downloadable example, see :ref:`here <example_discover>`.
