import pytest


def test_legacy_backend_plugin():
    import os
    import sys

    from edalize.edatool import get_edatools

    edatools = [x.__name__ for x in get_edatools()]
    # Test plugin should not be discovered yet
    assert "Testplugin" not in edatools

    # Copy original sys.path and add plugin path
    orgpath = sys.path.copy()
    sys.path.append(os.path.join(os.path.dirname(__file__), "test_plugin"))

    edatools = [x.__name__ for x in get_edatools()]
    # Test plugin should be in list now
    assert "Testplugin" in edatools

    # Restore original sys.path
    sys.path = orgpath


def test_flow_plugin():
    import os
    import sys

    with pytest.raises(ModuleNotFoundError):
        from edalize.flows.customexternalflow import Customexternalflow

    # Copy original sys.path and add plugin path
    orgpath = sys.path.copy()
    sys.path.append(os.path.join(os.path.dirname(__file__), "test_plugin"))

    # The import is the test: it must succeed with the plugin on sys.path
    from edalize.flows.customexternalflow import Customexternalflow  # noqa: F401

    # Restore original sys.path
    sys.path = orgpath


def test_tool_plugin():
    import os
    import sys

    with pytest.raises(ModuleNotFoundError):
        from edalize.tools.customtool import Customtool

    # Copy original sys.path and add plugin path
    orgpath = sys.path.copy()
    sys.path.append(os.path.join(os.path.dirname(__file__), "test_plugin"))

    # The import is the test: it must succeed with the plugin on sys.path
    from edalize.tools.customtool import Customtool  # noqa: F401

    # Restore original sys.path
    sys.path = orgpath
