from .edalize_tool_common import tool_fixture


def test_tool_icarus(tool_fixture):
    tool_name = "icarus"

    tool_options = {
        "timescale": "1ns/1ps",
        "iverilog_options": ["a", "few", "iverilog", "options"],
        "vvp_options": ["some", "vvp", "options"],
    }
    tf = tool_fixture(tool_name, tool_options=tool_options)

    tf.tool.configure()
    tf.compare_config_files(["design.scr"])

    tf.tool.run()


def test_tool_icarus_multiple_tops(tool_fixture):
    tf = tool_fixture(
        "icarus", toplevel=" ".join(["top1", "top2"]), ref_subdir="multitop"
    )

    tf.tool.configure()
    tf.compare_config_files(["design.scr"])

    tf.tool.run()
