from .edalize_tool_common import tool_fixture


def test_tool_sv2v(tool_fixture):
    tool_options = {
        "sv2v_options": ["some", "sv2v", "options"],
    }

    tf = tool_fixture("sv2v", tool_options=tool_options)

    tf.tool.configure()

    # The converted file is added to the output EDAM
    assert {"name": "design.v", "file_type": "verilogSource"} in tf.tool.edam["files"]


def test_tool_sv2v_minimal(tool_fixture):
    tf = tool_fixture("sv2v", ref_subdir="minimal")

    tf.tool.configure()
