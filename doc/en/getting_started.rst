Getting started
***************

Here is a step by step guide in order to install and try Testplan
in your local environment!

.. _install_testplan:

Install testplan
================

Ubuntu/Debian
-------------

First install required packages - you will need root privileges.

    .. code-block:: bash

      # For python 2.
      sudo apt-get install python python-pip rsync

      # For python 3.
      sudo apt-get install python3 python3-pip rsync


Native pip install
++++++++++++++++++

Install from archive:

    .. code-block:: bash

      # For python 2.
      pip install --user https://github.com/Morgan-Stanley/testplan/archive/master.zip
      install-testplan-ui

      # For python 3.
      pip3 install --user https://github.com/Morgan-Stanley/testplan/archive/master.zip
      install-testplan-ui


.. _using_virtualenv_ubuntu:

Using a virtualenv
++++++++++++++++++

Python 2
````````

    1. Install `virtualenv <https://virtualenv.pypa.io/en/stable>`_.

        .. code-block:: bash

          pip install virtualenv

    2. Create a virtualenv.

        .. code-block:: bash

          virtualenv testplan-oss
          cd testplan-oss
          source bin/activate

    3. Install testplan and its dependencies into the virtual env.

        .. code-block:: bash

          pip install https://github.com/Morgan-Stanley/testplan/archive/master.zip
          install-testplan-ui

Python 3
````````

    1. Create a virtualenv.

        .. code-block:: bash

          python3 -m venv testplan-oss
          cd testplan-oss
          source bin/activate

    2. Install testplan and its dependecies into the virtual env.

        .. code-block:: bash

          pip install https://github.com/Morgan-Stanley/testplan/archive/master.zip
          install-testplan-ui


Other Linux Distros
-------------------

For non-Debian Linux distributions you should be able to install using similar
steps as for Ubuntu/Debian - just check the docs for your distro's package
manager (e.g. yum, dnf, pacman) for how to install the required packages
instead of using apt-get.


MacOS
-----

Install `homebrew <https://brew.sh/>`_.

    .. code-block:: bash

        /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

Install `python <http://docs.python-guide.org/en/latest/starting/install/osx>`_:

   .. code-block:: bash

      # Python 2.
      brew install python@2

      # Python 3.
      brew install python


Native pip install
++++++++++++++++++

.. warning:: This will install testplan package with all the dependencies specified in the
             `requirements.txt <https://github.com/Morgan-Stanley/testplan/blob/master/requirements.txt>`_
             file. For a quick basic installation, also check the :ref:`using_virtualenv_macos` guide.

Install from archive.

    .. code-block:: bash

      # For python 2.
      sudo pip install https://github.com/Morgan-Stanley/testplan/archive/master.zip
      install-testplan-ui

      # For python 3.
      sudo pip3 install https://github.com/Morgan-Stanley/testplan/archive/master.zip
      install-testplan-ui


.. _using_virtualenv_macos:

Using a virtualenv
++++++++++++++++++


    1. Install `virtualenv <https://virtualenv.pypa.io/en/stable>`_.

        .. code-block:: bash

          # Python 2.
          pip install virtualenv

          # Python 3.
          pip3 install virtualenv

    2. Create a virtualenv.

        .. code-block:: bash

          virtualenv testplan-oss
          cd testplan-oss
          source bin/activate

    3. Clone testplan `repo <https://github.com/Morgan-Stanley/testplan>`_.

        .. code-block:: bash

          git clone https://github.com/Morgan-Stanley/testplan.git
          cd testplan

    4. Install dependecies and setup.

        .. code-block:: bash

          pip install .
          install-testplan-ui


Windows
-------

Using subsystem
+++++++++++++++

You can follow the ubuntu guide while using a windows
`subsystem <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.


Native pip install
++++++++++++++++++

For native installation using `pip <https://pypi.python.org/pypi/pip>`_
package management system:

    1. Install `git <https://git-scm.com/download/win>`_.
    2. Install `python <https://www.python.org/downloads>`_.
    3. Open the windows command prompt.
    4. Install `pip <https://pip.pypa.io/en/stable/installing>`_.

        .. code-block:: text

          C:\path\to\installed\interpreter\python.exe get-pip.py

    5. Install from archive.

        .. code-block:: text

          pip install https://github.com/Morgan-Stanley/testplan/archive/master.zip

.. warning::

  The ``install-testplan-ui`` currently can't be called on Windows after
  installing from archive. It will work if installed through virtualenv. If this
  isn't installed the ``--ui`` arg will not work properly (the web server will
  start but the UI won't load). Read more about the browser output
  :ref:`here <Output_Browser>`. Raise a GitHub issue if further assistance is
  needed.


Using a virtualenv
++++++++++++++++++

Installation using a `virtualenv <https://virtualenv.pypa.io/en/stable>`_:

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

    7. Clone testplan `repo <https://github.com/Morgan-Stanley/testplan>`_.

        .. code-block:: text

          git clone https://github.com/Morgan-Stanley/testplan.git
          cd testplan

    8. Install dependecies and setup.

        .. code-block:: text

          # Skip heavy dependencies but miss some functionality.
          pip install -r requirements-basic.txt
          python setup.py develop --no-deps
          python install-testplan-ui

Via Docker
==========

Installation
------------

To install docker, you can follow the instructions for your OS from this list:

    1. Ubuntu/Debian. For the latest available instructions, please visit the official `docker installation instructions for Ubuntu/Debian <https://docs.docker.com/install/linux/docker-ce/ubuntu/>`_.

        .. code-block:: bash

            sudo apt-get update
            sudo apt-get remove docker docker-engine docker.io
            sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
            sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
            sudo apt-get update
            sudo apt-get install docker-ce

            sudo usermod -aG docker $USER
            # now LOGOUT and LOGIN again!


    2. MacOS. For the latest available instructions, please visit the official `docker installation instructions for MacOS <https://docs.docker.com/docker-for-mac/install/>`_.

    3. Windows. For the latest available instructions, please visit the official `docker installation instructions for Windows <https://docs.docker.com/docker-for-windows/install/>`_.


Available images
----------------

Docker images for testplan are provided for two python versions, ``python2`` and
``python3``.

The images can be retrieved with the following commands:

    .. code-block:: bash

        # Python 2
        docker pull chiotis/testplan:2

        # Python 3
        docker pull chiotis/testplan:3



Interactive docker session
--------------------------

To try testplan in an interactive docker session, you can type:

    .. code-block:: bash

        docker run -it chiotis/testplan:2 bash

The source code is available to explore in ``/work``.


Docker batch execution
----------------------

To run testplan docker image in batch mode, you'll need to add your code as a
docker volume when running the image. If the  ``test_plan.py`` file is in ``$PWD``,
directory, the docker command will be:

    .. code-block:: bash

        # Example directory that contains test_plan.py file.
        cd examples/Assertions/Basic

        docker run -v $PWD:/work -it chiotis/testplan:2


If your testplan file has a name other than ``test_plan.py``, you can add it as an
argument in the ``docker run`` command:

    .. code-block:: bash

        # Example directory that contains test_plan.py file.
        cd examples/Assertions/Basic

        docker run -v $PWD:/work -it chiotis/testplan:2 ./my_test_plan.py


If you require special arguments for ``test_plan.py``, you can just append them
after the docker image:

    .. code-block:: bash

        # default test_plan.py
        docker run -v $PWD:/work -it chiotis/testplan:2 --pdf test.pdf

        # custom my_test_plan.py
        docker run -v $PWD:/work -it chiotis/testplan:2 ./my_test_plan.py --pdf test.pdf


Run testplan
============

Our examples
------------

There are some ready made examples demonstrating testplan
functonality/features and can be found within the
`repo <https://github.com/Morgan-Stanley/testplan>`_ under
``examples`` directory.

On Ubuntu/MacOS/etc:

    .. code-block:: bash

      # See all the examples categories.
      cd examples
      ls

      # Run an example demonstrating testplan assertions.
      cd Assertions/Basic
      ./test_plan.py

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
      python test_plan.py

    .. code-block:: text

      # Create a pdf report and open in automatically.
      python test_plan.py --pdf report.pdf -b


Also find all our downloadable examples :ref:`here <download>`.


Internal tests
--------------

To verify the correct setup process you can execute the internal unit/functional
tests. Some tests may be skipped due to optional dependency packages
(i.e sklearn used on 'Data Science' examples category).

    .. code-block:: text

        cd tests

        # Unit tests.
        pytest unit --verbose

        # Functional tests.
        pytest functional --verbose


Writing custom drivers
======================

Testplan drivers are designed to be able to be inherited/extended and create
new ones based on the user specific environment. Here is a section explaining
how to create drivers for
:ref:`custom applications and services <multitest_custom_drivers>`.
You can contribute missing drivers or improvements to the existing ones by
following the :ref:`contribution <contributing>` process.

Installing Testplan for development
===================================

If you would like to develop on testplan itself, great! You can follow the
relevant instructions above for installing testplan on your platform (Linux,
MacOS or Windows) - but instead of installing from the archive, clone the
repo with ``git`` and make a development install like:

    .. code-block:: bash

        git clone https://github.com/Morgan-Stanley/testplan.git
        cd testplan
        pip install -r requirements.txt
        install-testplan-ui --dev

Alternatively, you can pull and run a portable testplan dev env using ``docker``.
See section on ``docker`` above for instructions on installing ``docker`` itself,
then you can simply run:

    .. code-block:: bash

        docker pull ryancollingham/dev_env:testplan
        docker run -it ryancollingam/dev_env:testplan

That will drop you into a shell with the testplan dependencies pre-installed,
the testplan codebase checked out and installed in a development (i.e. editable)
mode, and some other useful development tools installed. This dockerised environment
is shell-only so you can use the installed ``vim`` editor to edit code
(of course ``emacs`` developers are also welcome on testplan).

