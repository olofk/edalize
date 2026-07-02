from .edalize_tool_common import tool_fixture


def test_tool_ghdl(tool_fixture):
    tool_options = {
        "analyze_options": ["some", "analyze_options"],
        "run_options": ["a", "few", "run_options"],
    }

    tf = tool_fixture("ghdl", tool_options=tool_options)

    tf.tool.configure()

    tf.tool.run()


def test_tool_ghdl_std_override(tool_fixture):
    tool_options = {
        "analyze_options": ["--std=93", "--ieee=synopsys"],
    }

    tf = tool_fixture("ghdl", tool_options=tool_options, ref_subdir="stdoverride")

    tf.tool.configure()


def test_tool_ghdl_verilog(tool_fixture):
    tool_options = {"mode": "verilog"}

    tf = tool_fixture("ghdl", tool_options=tool_options, ref_subdir="verilog")

    tf.tool.configure()


def test_tool_ghdl_toplevel_library(tool_fixture):
    tf = tool_fixture("ghdl", toplevel="libx.vhdl_lfile", ref_subdir="toplib")

    tf.tool.configure()
