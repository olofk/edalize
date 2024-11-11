from .edalize_tool_common import tool_fixture


def test_tool_verilator(tool_fixture):

    tool_options = {
        "make_options": ["a", "few", "make", "options"],
        "verilator_options": ["some", "verilator", "options"],
        "run_options": ["and", "some", "run", "options"],
    }

    tf = tool_fixture("verilator", tool_options=tool_options)

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + ".vc",
        ]
    )


def test_tool_verilator_minimal(tool_fixture):
    tf = tool_fixture("verilator", ref_subdir="minimal")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + ".vc",
        ]
    )
