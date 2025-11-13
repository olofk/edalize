import pytest
from .edalize_tool_common import tool_fixture


def test_tool_openfpgaloader_gowin(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "bit.fs", "file_type": "gowinFusesFile"})

    tool_options = {"board": "tangnano9k"}

    tf = tool_fixture(
        "openfpgaloader",
        files=files,
        tool_options=tool_options,
        ref_subdir="gowin-tangnano9k",
    )

    tf.tool.configure()


def test_tool_openfpgaloader_gowin_no_file(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("openfpgaloader", files=[], ref_subdir="gowin-error")
    assert "No input file specified for openFPGAloader" in str(e.value)
