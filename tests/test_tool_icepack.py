import pytest
from .edalize_tool_common import tool_fixture


def test_tool_icepack(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "asc_file.asc", "file_type": "iceboxAscii"})

    tf = tool_fixture("icepack", files=files)

    tf.tool.configure()


def test_tool_icepack_no_input(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tool = tool_fixture("icepack", files=[])
    assert "No input file specified for icepack" in str(e.value)


def test_tool_icepack_multiple_inputs(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "asc_file.asc", "file_type": "iceboxAscii"})
    files.append({"name": "another_asc_file.asc", "file_type": "iceboxAscii"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("icepack", files=files)
    assert (
        "Icepack only supports one input file. Found asc_file.asc and another_asc_file.asc"
        in str(e.value)
    )
