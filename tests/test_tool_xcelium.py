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


def test_tool_xcelium_minimal(tool_fixture):
    tf = tool_fixture("xcelium", tool_options={}, paramtypes=[], ref_subdir="minimal")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "xrun.f",
        ]
    )
