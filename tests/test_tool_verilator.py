from .edalize_tool_common import tool_fixture


def test_tool_verilator(tool_fixture):
    tf = tool_fixture("verilator")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + ".vc",
        ]
    )
