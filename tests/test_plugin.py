import pytest


def test_legacy_backend_plugin():
    import os
    import sys
    from pkgutil import walk_packages
    from edalize.edatool import get_edatools

    edatools = [x.__name__ for x in get_edatools()]
    # Test plugin should not be discovered yet
    assert not "Testplugin" in edatools

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

    from edalize.flows.customexternalflow import Customexternalflow

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

    from edalize.tools.customtool import Customtool

    # Restore original sys.path
    sys.path = orgpath
