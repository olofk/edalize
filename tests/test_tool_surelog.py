from .edalize_tool_common import tool_fixture


def test_tool_surelog(tool_fixture):
    tool_name = "surelog"

    tool_options = {
        "surelog_options": ["a", "few", "surelog", "options"],
    }
    tf = tool_fixture(tool_name, tool_options=tool_options)

    tf.tool.configure()
