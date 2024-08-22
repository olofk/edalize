from .edalize_tool_common import tool_fixture


def test_tool_modelsim(tool_fixture):
    tool_name = "modelsim"

    # "compilation_mode": {
    # "desc": "Common or separate compilation, sep - for separate compilation, common - for common compilation",
    tool_options = {
        "vcom_options": ["several", "vcom", "options"],
        "vlog_options": ["a", "few", "vlog", "options"],
        "vsim_options": ["some", "vsim", "options"],
    }
    tf = tool_fixture(tool_name, tool_options=tool_options)

    tf.tool.configure()
    tf.compare_config_files(["edalize_build_rtl.tcl", "edalize_main.tcl"])

    tf.tool.run()


def test_tool_modelsim_mfcu(tool_fixture):
    tool_name = "modelsim"

    # "compilation_mode": {
    # "desc": "Common or separate compilation, sep - for separate compilation, common - for common compilation",
    tool_options = {
        "compilation_mode": "common",
        "vcom_options": ["several", "vcom", "options"],
        "vlog_options": ["a", "few", "vlog", "options"],
        "vsim_options": ["some", "vsim", "options"],
    }
    tf = tool_fixture(tool_name, tool_options=tool_options, ref_subdir="mfcu")

    tf.tool.configure()
    tf.compare_config_files(["edalize_build_rtl.tcl", "edalize_main.tcl"])

    tf.tool.run()
