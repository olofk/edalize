***************
Testing edalize
***************

Users
=====

To run the tests, call :command:`pytest`.

Developers
==========

Mocks for commands
------------------

We provide mocks (stand-ins) for all tools that we want to exercise in tests (located in :file:`tests/mock_commands/`).
These mocks are very simplified "models" of the actual tool, and are called instead of the actual tool
(the :func:`edalize_common.setup_backend` and :func:`edalize_common.setup_backend` functions prepend them to :envvar:`PATH`).

In the easiest case, these mocks just write out the commandline they were called with (into a file :file:`<tool>.cmd`).

In a more complex test setup (e.g. for ``vcs``),

* if a tool is creating files, we create it too (the file to create is taken from a tool option given)
* we make the file executable
* we set the access and modified times of generated files to the current time

Testcases
---------

A testcase (being run with :command:`pytest`) is usually calling the tool to be tested via :func:`edalize_common.setup_backend`.
Instead of the actual tool, the tool mock is used.

The output of the tool mock is compared (using :func:`edalize_common.compare_files`)
with the reference files in :file:`tests/test_<tool>/<testcase>/*`.

If the environment variable :envvar:`GOLDEN_RUN` is set,
the generated files are copied to become the new reference files in this step.


Helper Module
=============

edalize_common
--------------

.. automodule:: edalize_common
    :members:
    :undoc-members:
    :member-order: bysource
    :show-inheritance:
