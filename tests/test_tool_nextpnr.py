import pytest

from .edalize_tool_common import tool_fixture


def test_tool_nextpnr_noarch(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tool = tool_fixture("nextpnr")
    assert "nextpnr requires tool option 'arch'" in str(e.value)


def test_tool_nextpnr_wrongarch(tool_fixture):
    tool_options = {"arch": "wrong"}
    with pytest.raises(RuntimeError) as e:
        tool = tool_fixture("nextpnr", tool_options=tool_options)
    assert "Invalid arch. Allowed options are " in str(e.value)


def test_tool_nextpnr_minimal(tool_fixture):
    tool_options = {"arch": "ice40"}

    tf = tool_fixture("nextpnr", tool_options=tool_options, ref_subdir="minimal")

    tf.tool.configure()


def test_tool_nextpnr_ecp5(tool_fixture):
    tool_options = {"arch": "ecp5"}
    tf = tool_fixture("nextpnr", tool_options=tool_options, ref_subdir="ecp5")
    tf.tool.configure()
