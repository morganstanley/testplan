Getting started
***************

Here is a step by step guide in order to install and try Testplan
in your local environment!

.. _supported_python_versions:

Supported Python Versions
=========================

Testplan is tested to work with Python 3.9+ so we recommend choosing one of those.

.. _install_testplan:

Install testplan
================

Testplan is available from pypi.org: https://pypi.org/project/testplan/

    .. code-block:: bash

      python3 -m pip install testplan


Alternatively, one can install it from the latest github package. A link for our lates package can be obtained from: https://github.com/morganstanley/testplan/releases/tag/latest

Install from archive:
  
    .. code-block:: bash

      python3 -m pip install https://github.com/morganstanley/testplan/releases/download/24.9.2/testplan-24.9.2-py3-none-any.whl
      

Run testplan
============

Our examples
------------

There are some ready made examples demonstrating testplan
functonality/features and can be found within the
`repo <https://github.com/morganstanley/testplan>`_ under
``examples`` directory.

On Ubuntu/MacOS/etc:

    .. code-block:: bash

      # See all the examples categories.
      cd examples
      ls

      # Run an example demonstrating testplan assertions.
      cd Assertions/Basic
      ./test_plan_basic.py

    .. code-block:: bash

      # Create a pdf report and open in automatically.
      ./test_plan.py --pdf report.pdf -b

On Windows:

    .. code-block:: text

      # See all the examples categories.
      cd examples
      dir

      # Run an example demonstrating testplan assertions.
      cd Assertions\Basic
      python test_plan_basic.py

    .. code-block:: text

      # Create a pdf report and open in automatically.
      python test_plan.py --pdf report.pdf -b


Also find all our downloadable examples :ref:`here <download>`.


Working with the source
-----------------------
 
You will need a working Python 3 interpreter preferably a venv, and for the interactive ui you need Node.js installed. 
We are using `doit <https://pydoit.org/contents.html>`_ as the taskrunner ``doit list`` can show all the commands.

  .. code-block:: text
      
    git clone https://github.com/morganstanley/testplan.git
    cd testplan

    # install testplan in editable mode & all dev requirements
    pip install -e .

    # build the interactive UI (if you do not like it is opening a browserwindow remove the `-o`)
    doit build_ui -o

Internal tests
--------------

To verify the correct setup process you can execute the internal unit/functional
tests. Some tests may be skipped due to optional dependency packages
(i.e sklearn used on 'Data Science' examples category).

    .. code-block:: text

      doit test


Writing custom drivers
======================

Testplan drivers are designed to be able to be inherited/extended and create
new ones based on the user specific environment. Here is a section explaining
how to create drivers for
:ref:`custom applications and services <multitest_custom_drivers>`.
You can contribute missing drivers or improvements to the existing ones by
following the :ref:`contribution <contributing>` process.
