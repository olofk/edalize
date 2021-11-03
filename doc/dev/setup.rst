Development Setup
=================

Setup development environment
-----------------------------

.. note::

   If you have already installed Edalize, remove it first using ``pip3 uninstall edalize``.

To develop Edalize and test the changes, the edalize package needs to be installed in editable or development mode.
In this mode, the ``edalize`` command is linked to the source directory, and changes made to the source code are
immediately visible when calling ``edalize``.

.. code-block:: bash

   # Install all Python packages required to develop edalize
   pip3 install --user -r dev-requirements.txt

   # Install Git pre-commit hooks, e.g. for the code formatter and lint tools
   pre-commit install

   # Install the edalize package in editable mode
   pip3 install --user -e .

.. note::

    All commands above use Python 3 and install software only for the current user.
    If, after this installation, the ``edalize`` command cannot be found adjust your ``PATH`` environment variable to
    include ``~/.local/bin``.

After this installation is completed, you can

* edit files in the source directory and re-run ``edalize`` to immediately see the changes,
* run the unit tests as outlined in the section below, and
* use linter and automated code formatters.

Formatting and linting code
---------------------------

The Edalize code comes with tooling to automatically format code to conform to our expectations.
These tools are installed and called through a tool called `pre-commit <https://pre-commit.com/>`_.
No setup is required: whenever you do a ``git commit``, the necessary tools are called and your code is automatically formatted and checked for common mistakes.

To check the whole source code ``pre-commit`` can be run directly:

.. code-block:: bash

   # check and fix all files
   pre-commit run -a
