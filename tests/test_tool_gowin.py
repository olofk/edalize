from .edalize_tool_common import tool_fixture


def test_tool_gowin(tool_fixture):

    tool_options = {
        "part": "dummy_part",
        "gowin_options": ["some", "gowin", "options"],
    }

    tf = tool_fixture(
        "gowin", tool_options=tool_options, paramtypes=[], has_makefile=False
    )

    tf.tool.configure()
    tf.compare_config_files(["edalize_gowin_template.tcl"])


def test_tool_gowin_minimal(tool_fixture):
    tool_options = {"part": "dummy_part"}
    tf = tool_fixture(
        "gowin",
        tool_options=tool_options,
        ref_subdir="minimal",
        paramtypes=[],
        has_makefile=False,
    )

    tf.tool.configure()
    tf.compare_config_files(["edalize_gowin_template.tcl"])
