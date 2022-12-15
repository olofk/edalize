import os
import pytest
from .edalize_common import make_edalize_test, tests_dir


def run_symbiflow_test(tf, config_files=list()):
    config_files_list = config_files + ["Makefile"]
    tf.backend.configure()
    tf.compare_files(config_files_list)


def test_symbiflow_vtr(make_edalize_test):
    tool = "symbiflow"
    tool_options = {
        "part": "xc7a35tcsg324-1",
        "package": "csg324-1",
        "vendor": "xilinx",
        "pnr": "vtr",
        "vpr_options": "--fake_option 1000",
    }

    files = [
        {"name": "top.xdc", "file_type": "xdc"},
        {"name": "top.sdc", "file_type": "SDC"},
        {"name": "top.pcf", "file_type": "PCF"},
    ]
    tf = make_edalize_test(
        "symbiflow",
        test_name="test_symbiflow_vtr_0",
        param_types=["vlogdefine", "vlogparam"],
        tool_options=tool_options,
        files=files,
        ref_dir="vtr",
    )

    run_symbiflow_test(tf)


def test_symbiflow_nextpnr_xilinx(make_edalize_test):
    tool = "symbiflow"
    tool_options = {
        "arch": "xilinx",
        "part": "xc7a35tcsg324-1",
        "package": "csg324-1",
        "vendor": "xilinx",
        "pnr": "nextpnr",
        "nextpnr_options": "--fake_option 1000",
    }

    files = [
        {"name": "top.xdc", "file_type": "xdc"},
        {"name": "chipdb.bin", "file_type": "bba"},
    ]

    test_name = "test_symbiflow_nextpnr_xilinx_0"
    tf = make_edalize_test(
        "symbiflow",
        test_name=test_name,
        param_types=["vlogdefine", "vlogparam"],
        tool_options=tool_options,
        files=files,
        ref_dir=os.path.join("nextpnr", "xilinx"),
    )

    config_files = [
        "edalize_yosys_procs.tcl",
        "edalize_yosys_template.tcl",
    ]

    run_symbiflow_test(tf, config_files)


def test_symbiflow_nextpnr_fpga_interchange(make_edalize_test):
    tool = "symbiflow"
    tool_options = {
        "arch": "fpga_interchange",
        "part": "xc7a35tcsg324-1",
        "package": "csg324-1",
        "vendor": "xilinx",
        "pnr": "nextpnr",
        "nextpnr_options": "--fake_option 1000",
    }

    files = [
        {"name": "top.xdc", "file_type": "xdc"},
        {"name": "chipdb.bin", "file_type": "bba"},
        {"name": "xc7a35t.device", "file_type": "device"},
    ]

    test_name = "test_symbiflow_nextpnr_fpga_interchange_0"
    tf = make_edalize_test(
        "symbiflow",
        test_name=test_name,
        param_types=["vlogdefine", "vlogparam"],
        tool_options=tool_options,
        files=files,
        ref_dir=os.path.join("nextpnr", "fpga_interchange"),
    )

    config_files = [
        "edalize_yosys_procs.tcl",
        "edalize_yosys_template.tcl",
    ]

    orig_env = os.environ.copy()
    try:
        os.environ["INTERCHANGE_SCHEMA_PATH"] = os.path.join(tests_dir, "mock_commands")
        run_symbiflow_test(tf, config_files)
    finally:
        os.environ = orig_env
