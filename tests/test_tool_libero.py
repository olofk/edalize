from .edalize_tool_common import tool_fixture


libero_files=[
    {"name": "sdc_file.sdc", "file_type": "SDC"},
    {"name": "sv_file.sv", "file_type": "systemVerilogSource"},
    {"name": "vlog_file.v", "file_type": "verilogSource"},
    {"name": "tcl_file.tcl", "file_type": "tclSource"},
    {
        "name": "vlog_with_define.v",
        "file_type": "verilogSource",
        "define": {"FD_KEY": "FD_VAL"},
    },
    {"name": "vlog05_file.v", "file_type": "verilogSource-2005"},
    {"name": "vhdl_file.vhd", "file_type": "vhdlSource"},
    {"name": "vhdl_lfile", "file_type": "vhdlSource", "logical_name": "libx"},
    {"name": "another_sv_file.sv", "file_type": "systemVerilogSource"},
    {"name": "pdc_constraint_file.pdc", "file_type": "PDC"},
    {"name": "pdc_floorplan_constraint_file.pdc", "file_type": "FPPDC"},
]

def test_tool_libero(tool_fixture):
    """Test passing tool options to the Libero tool backend"""
    name = "design"
    tool_options = {"family": "PolarFire", "die": "MPF300TS_ES", "package": "FCG1152"}

    tf = tool_fixture("libero", tool_options=tool_options, files=libero_files, ref_subdir="base")

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + "-project.tcl",
            name + "-syn-user.tcl",
            name + "-build.tcl",
        ]
    )

def test_tool_libero_with_params(tool_fixture):
    """Test passing tool options to the Libero tool backend."""

    name = "design"
    tool_options = {
        "family": "PolarFire",
        "die": "MPF300TS_ES",
        "package": "FCG1152",
        "speed": "-1",
        "dievoltage": "1.0",
        "range": "EXT",
        "defiostd": "LVCMOS 1.8V",
        "hdl": "VHDL",
    }

    tf = tool_fixture("libero", tool_options=tool_options, files=libero_files, ref_subdir="all-options")

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + "-project.tcl",
            name + "-syn-user.tcl",
            name + "-build.tcl",
        ]
    )
