import pytest
from .edalize_tool_common import tool_fixture


def test_tool_ecppack(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "design.config", "file_type": "nextpnrTrellisConfig"})

    tf = tool_fixture("ecppack", files=files)

    tf.tool.configure()


def test_tool_ecppack_no_input(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("ecppack", files=[])
    assert "No input file specified for ecppack" in str(e.value)


def test_tool_ecppack_multiple_inputs(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "a.config", "file_type": "nextpnrTrellisConfig"})
    files.append({"name": "b.config", "file_type": "nextpnrTrellisConfig"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("ecppack", files=files)
    assert "ecppack only supports one input file. Found a.config and b.config" in str(
        e.value
    )
