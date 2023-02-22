from .edalize_tool_common import tool_fixture


def test_tool_icarus(tool_fixture):
    tool_name = "icarus"

    tf = tool_fixture(tool_name)

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
