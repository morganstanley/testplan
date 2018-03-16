Generate documentation
======================
From project root directory:

::

    cd doc/en
    rm -rf ../../../build/html; ../../ms/scripts/bin/gen_docs.py -b html . ../../../build/html
    firefox ../../../build/html/index.html


Execute unit tests
==============
From project root directory, run all Python 2 & 3 tests:

::

    ./ms/scripts/bin/pytest_top_level


Execute one test
----------------
::

    cd ms/scripts/bin
    python run_pytest functional/testplan/runners/pools/test_pool_process.py


Execute an example
==================

::

    cd testplan/examples/Transports/TCP
    python ../../../../ms/scripts/bin/run_testplan.py ./test_plan.py --verbose


Pycharm setup (Windows)
==============

Setup a script for python 2 top level
-------------------------------------
    Script:
    X:\PATH\TO\ms\scripts\bin\run_pytest

    Interpreter:
    path to python .exe 2.7.9

    Working directory:
    PATH/TO/ms\scripts\bin


Setup a script for python 3 top level
-------------------------------------
    Script:
    X:\PATH\TO\ms\scripts\bin\run_pytest

    Interpreter:
    path to python .exe 3.4.2

    Working directory:
    PATH/TO/ms\scripts\bin

    Before launch:
    Run top level for python 2


Setup two scripts for python 2/3 single test
--------------------------------------------
    Script:
    X:\PATH\TO\ms\scripts\bin\run_pytest

    Script parameters:
    functional\testplan\runners\pools\test_pool_process.py

    Interpreter:
    path to python .exe 2.7.9/3.4.2

    Working directory:
    PATH/TO/ms\scripts\bin


Setup script for downloadable example
-------------------------------------
    Script:
    ..\..\..\..\ms\scripts\bin\run_testplan.py

    Script parameters:
    test_plan.py --debug

    Interpreter:
    path to python .exe 2.7.9/3.4.2

    Working directory:
    X:\PATH\TO\testplan\examples\Transports\TCP
