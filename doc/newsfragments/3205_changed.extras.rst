Move certain dependencies to extras (i.e. optional dependencies) to shrink the installation size in pipelines. User need to install Testplan with extras in order to use certain features.

* Extra ``interactive`` for interactive mode & report display through local server features, containing ``flask`` & several related packages.
* Extra ``plotly`` for plotting with plotly feature, containing ``pandas`` & ``plotly``.
* Extra ``all`` for all the features above.

For example, to use interactive mode feature, one can install Testplan with the following command:

.. code-block:: bash

    pip install testplan[interactive]
