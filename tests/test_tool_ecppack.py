import pytest
from .edalize_tool_common import tool_fixture


def test_tool_ecppack(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "routed.json", "file_type": "nextpnrRoutedJson"})

    tf = tool_fixture("ecppack", files=files)

    tf.tool.configure()


def test_tool_ecppack_no_input(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("ecppack", files=[])
    assert "No input file specified for ecppack" in str(e.value)


def test_tool_ecppack_multiple_inputs(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "routed.json", "file_type": "nextpnrRoutedJson"})
    files.append({"name": "another_routed.json", "file_type": "nextpnrRoutedJson"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("ecppack", files=files)
    assert (
        "ecppack only supports one input file. Found routed.json and another_routed.json"
        in str(e.value)
    )
