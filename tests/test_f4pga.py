import os
import pytest
from edalize_common import make_edalize_test, tests_dir

def run_f4pga_test(tf, config_files=list()):
    config_files_list = config_files + ["Makefile"]
    tf.backend.configure()
    tf.compare_files(config_files_list)

def test_f4pga_vpr(make_edalize_test):
    tool = "f4pga"
    tool_options = {
        'arch': 'xilinx',
        'device_type': 'artix7',
        'device_name': 'xc7a50t_test',
        'part' : 'xc7a35tcpg236-1',
        'pnr' : 'vpr'
    }

    files = [
        {"name": "top.xdc", "file_type": "xdc"},
        {"name": "top.v", "file_type": "verilogSource"}
    ]

    tf = make_edalize_test(
        "f4pga",
        test_name="test_f4pga_vpr_0",
        param_types=[],
        tool_options=tool_options,
        files=files,
        ref_dir="vpr"
    )

    config_files = [
        "openocd.txt"
    ]

    run_f4pga_test(tf, config_files)

def test_f4pga_nextpnr(make_edalize_test):
    tool = "f4pga"
    tool_options = {
        'arch': 'xilinx',
        'device_type': 'artix7',
        'device_name': 'xc7a50t_test',
        'part' : 'xc7a35tcpg236-1',
        'pnr' : 'nextpnr'
    }

    files = [
        {"name": "top.xdc", "file_type": "xdc"},
        {"name": "top.v", "file_type": "verilogSource"},
        {"name": "board.bin", "file_type": "bin"}
    ]

    tf = make_edalize_test(
        "f4pga",
        test_name="test_f4pga_nextpnr_0",
        param_types=[],
        tool_options=tool_options,
        files=files,
        ref_dir="nextpnr"
    )

    config_files = [
        "edalize_yosys_procs.tcl",
        "openocd.txt"
    ]

    run_f4pga_test(tf, config_files)