import pytest
from .edalize_tool_common import tool_fixture


def test_tool_icetime(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "asc_file.asc", "file_type": "iceboxAscii"})

    tf = tool_fixture("icetime", files=files)

    tf.tool.configure()

    # The timing report is added to the output EDAM
    assert {"name": "asc_file.tim", "file_type": "report"} in tf.tool.edam["files"]


def test_tool_icetime_no_input(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("icetime", files=[])
    assert "No input file specified for icetime" in str(e.value)


def test_tool_icetime_multiple_inputs(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "asc_file.asc", "file_type": "iceboxAscii"})
    files.append({"name": "another_asc_file.asc", "file_type": "iceboxAscii"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("icetime", files=files)
    assert (
        "Icetime only supports one input file. Found asc_file.asc and another_asc_file.asc"
        in str(e.value)
    )
