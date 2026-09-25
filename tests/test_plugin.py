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


def test_tool_plugin(tmp_path, monkeypatch):
    import os

    from edalize.flows.generic import Generic

    with pytest.raises(ModuleNotFoundError):
        from edalize.tools.customtool import Customtool

    monkeypatch.syspath_prepend(os.path.join(os.path.dirname(__file__), "test_plugin"))

    from edalize.tools.customtool import Customtool

    edam = {"name": "design", "files": [], "flow_options": {"tool": "customtool"}}
    flow = Generic(edam, tmp_path)
    flow.configure()
    flow.build()
    assert (tmp_path / "design.count").read_text().split() == ["1", "design.cfg"]
