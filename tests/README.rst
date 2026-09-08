Testing edalize
###############

To run the tests, call :command:`pytest`.


Mocks for commands
==================

We provide mocks (stand-ins) for all tools that we want to exercise in tests (located in :file:`tests/mock_commands/`).
These mocks are very simplified "models" of the actual tool, and are called instead of the actual tool.
They are prepended to :envvar:`PATH` by the setup code in the :func:`edalize_common.make_edalize_test` pytest fixture.

In the easiest case, these mocks just write out the commandline they were called with (into a file :file:`<tool>.cmd`).

In a more complex test setup (e.g. for ``vcs``),

* if a tool is creating files, we create it too (the file to create is taken from a tool option given)
* we make the file executable
* we set the access and modified times of generated files to the current time


Testcases
=========

Tests for legacy backends use the
:func:`edalize_common.make_edalize_test` pytest factory fixture. This defines a
factory that sets up a mocked backend. See
:py:class:`edalize_common.TestFixture` for the supported keywords. The
:py:attr:`backend` attribute of the returned fixture has
:py:meth:`configure`, :py:meth:`build`, and :py:meth:`run` methods. Call the
applicable phases in order, set up files as necessary between calls, and check
the results with :py:meth:`compare_files`.

Tests for modern tool nodes use the ``tool_fixture`` fixture from
``edalize_tool_common``. Tests for flows use the ``flow_fixture`` fixture from
``edalize_flow_common``. These fixtures construct EDAM through the shared test
infrastructure and expose ``tool`` or ``flow`` objects, respectively. Compare
generated Makefiles and configuration files with their fixture comparison
helpers. When a flow test executes a mocked command, prepend the tracked
``tests/mock_commands`` directory to ``PATH`` with pytest's ``monkeypatch``
fixture.

If the environment variable :envvar:`GOLDEN_RUN` is set, the :py:meth:`compare_files` method copies the generated files are copied to become the new reference files, rather than checking their contents.


Helper Module
=============

edalize_common
--------------

.. automodule:: edalize_common
    :members:
    :undoc-members:
    :member-order: bysource
    :show-inheritance:
