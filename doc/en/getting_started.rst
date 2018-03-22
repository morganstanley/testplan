Getting started
***************

Here is a step by step guide in order to install and try Testplan
in your local environment!


Install testplan
================

Ubuntu/Debian
-------------

Using a `virtualenv <https://virtualenv.pypa.io/en/stable>`_
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Install `git <https://git-scm.com/>`_.

    .. code-block:: bash

      sudo apt-get install git

Python 2
````````

    1. Install `pip <https://pypi.python.org/pypi/pip>`_.

        .. code-block:: bash

          sudo apt-get install python-pip

    2. Install `virtualenv <https://virtualenv.pypa.io/en/stable>`_.

        .. code-block:: bash

          pip install virtualenv

    3. Create a virtualenv.

        .. code-block:: bash

          virtualenv testplan-oss
          cd testplan-oss
          source bin/activate

    4. Clone testplan `repo <https://github.com/Morgan-Stanley/testplan>`_.

        .. code-block:: bash

          git clone https://github.com/Morgan-Stanley/testplan.git
          cd testplan

    5. Install dependecies and setup.

        .. code-block:: bash

          # skip heavy dependencies but miss some functionality
          pip install -r requirements-basic.txt
          python setup.py develop --no-deps

        .. code-block:: bash

          # make a full setup
          pip install -r requirements.txt
          python setup.py develop

Python 3
````````

    1. Install `pip3 <https://pypi.python.org/pypi/pip>`_.
        
        .. code-block:: bash

          sudo apt-get install python3-pip

    2. Install `virtualenv <https://virtualenv.pypa.io/en/stable>`_.

        .. code-block:: bash

          pip3 install virtualenv

    3. Create a virtualenv.

        .. code-block:: bash

          virtualenv -p python3 testplan-oss
          cd testplan-oss
          source bin/activate

    4. Clone testplan `repo <https://github.com/Morgan-Stanley/testplan>`_.

        .. code-block:: bash

          git clone https://github.com/Morgan-Stanley/testplan.git
          cd testplan

    5. Install dependecies and setup.

        .. code-block:: bash

          # Skip heavy dependencies but miss some functionality.
          pip3 install -r requirements-basic.txt
          python setup.py develop --no-deps

          # Or, make a full setup
          pip3 install -r requirements.txt
          python setup.py develop


Full setup
``````````
In order to setup testplan with all its dependencies you need to use
``requirements.txt`` file instead of ``requirements-basic.txt``.
You may also need to ``sudo apt-get install`` some packages
like: ``python-tk``/``python3-tk``.


Run examples
````````````

You can run some ready made examples from inside the repo.

    .. code-block:: bash
      
      # These are all the examples categories.  
      cd testplan/examples
      ls

      # Run an example demonstrating testplan assertions.
      cd Assertions/Basic
      ./test_plan.py

    .. code-block:: bash
      
      # Create a pdf report and open in automatically.
      ./test_plan.py --pdf report.pdf -b


Also find all our downloadable examples :ref:`here <download>`.


Run the tests
`````````````

You can run the unit/functional tests to verify the correct repo setup.
Some tests may be skipped due to optional dependency packages.

    .. code-block:: bash
      
        cd test

        # Unit tests.
        py.test unit --verbose

        # Functional tests.
        py.test functional --verbose


Windows
-------

Using subsystem
+++++++++++++++

You can follow the ubuntu guide while using a windows
`subsystem <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.


Using a `virtualenv <https://virtualenv.pypa.io/en/stable>`_
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To try Testplan in a windows environment:

    1. Install `git <https://git-scm.com/download/win>`_.
    2. Install `python <https://www.python.org/downloads>`_.
    3. Open the windows command prompt.
    4. Install `pip <https://pip.pypa.io/en/stable/installing>`_.

        .. code-block:: text
      
          C:\path\to\installed\interpreter\python.exe get-pip.py

    5. Install `virtualenv <https://virtualenv.pypa.io/en/stable>`_.

        .. code-block:: text

          pip install virtualenv

    6. Create a virtualenv.

        .. code-block:: text

          virtualenv -p C\:path\to\installed\interpreter\python.exe testplan-oss
          cd testplan-oss
          .\Scripts\activate

    4. Clone testplan `repo <https://github.com/Morgan-Stanley/testplan>`_.

        .. code-block:: text

          git clone https://github.com/Morgan-Stanley/testplan.git
          cd testplan

    5. Install dependecies and setup.

        .. code-block:: text

          # Skip heavy dependencies but miss some functionality.
          pip install -r requirements-basic.txt
          python setup.py develop --no-deps


Run examples
````````````

You can run some ready made examples from inside the repo.

    .. code-block:: text
      
      # These are all the examples categories.  
      cd testplan\examples
      ls

      # Run an example demonstrating testplan assertions.
      cd Assertions\Basic
      python test_plan.py

    .. code-block:: text
      
      # Create a pdf report and open in automatically.
      python test_plan.py --pdf report.pdf -b


Also find all our downloadable examples :ref:`here <download>`.


Run the tests
`````````````

You can run the unit/functional tests to verify the correct repo setup.
Some tests may be skipped due to optional dependency packages.

    .. code-block:: text
      
        cd test

        # Unit tests.
        py.test unit --verbose

        # Functional tests.
        py.test functional --verbose


Writing custom drivers
======================

Testplan drivers are designed to be able to be inherited/extended and create
new ones based on the user specific environment. Here is a section explaining
how to create drivers for
:ref:`custom applications and services <multitest_custom_drivers>`.
You can contribute missing drivers or improvements to the existing ones by
following the :ref:`contribution <contributing>` process.
