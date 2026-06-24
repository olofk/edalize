import pytest

from .edalize_tool_common import tool_fixture


def test_tool_xcelium(tool_fixture):

    tool_options = {
        "32bit": True,
        "timescale": "2beardseconds/1fortnight",
        "xrun_options": ["some", "xrun", "options"],
    }

    tf = tool_fixture("xcelium", tool_options=tool_options)

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "xrun.f",
        ]
    )

    cmd, args, _ = tf.tool.run()
    assert cmd == "xrun"
    assert "-R" in args
    assert "-input" in args
    assert args[args.index("-input") + 1] == "tcl_file.tcl"


def test_tool_xcelium_minimal(tool_fixture):
    tf = tool_fixture("xcelium", tool_options={}, paramtypes=[], ref_subdir="minimal")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "xrun.f",
        ]
    )

    cmd, args, _ = tf.tool.run()
    assert cmd == "xrun"
    assert "-R" in args
    assert "-input" in args
    assert args[args.index("-input") + 1] == "tcl_file.tcl"


@pytest.mark.parametrize("gui", (None, False, True))
def test_tool_xcelium_gui(tool_fixture, gui: bool | None) -> None:
    """Test if the Xcelium backend will add the ``-gui`` option."""
    tool_options = {}

    if gui is not None:
        tool_options["gui"] = gui

    tf = tool_fixture("xcelium", tool_options=tool_options, paramtypes=[])

    tf.tool.configure()
    command, args, _ = tf.tool.run()

    assert command == "xrun"

    if gui:
        assert "-gui" in args
    else:
        assert "-gui" not in args
