from .edalize_common import make_edalize_test

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

def test_libero(make_edalize_test):
    """Test passing tool options to the Libero backend"""
    name = "libero-test"
    tool_options = {"family": "PolarFire", "die": "MPF300TS_ES", "package": "FCG1152"}

    tf = make_edalize_test("libero", test_name=name, tool_options=tool_options, files=libero_files)

    tf.backend.configure()
    tf.compare_files(
        [
            name + "-project.tcl",
            name + "-build.tcl",
            name + "-run.tcl",
            name + "-syn-user.tcl",
        ]
    )


def test_libero_with_params(make_edalize_test):
    """Test passing tool options to the Libero backend"""
    name = "libero-test-all"
    tool_options = {
        "family": "PolarFire",
        "die": "MPF300TS_ES",
        "package": "FCG1152",
        "speed": "-1",
        "dievoltage": "1.0",
        "range": "EXT",
        "defiostd": "LVCMOS 1.8V",
        "hdl": "VHDL",
        "programmer": "E2008ETVQU",
        "flashpro5_freq": "15000000",
    }

    tf = make_edalize_test("libero", test_name=name, tool_options=tool_options, files=libero_files)

    tf.backend.configure()
    tf.compare_files(
        [
            name + "-project.tcl",
            name + "-build.tcl",
            name + "-run.tcl",
            name + "-syn-user.tcl",
        ]
    )
