import os
import pytest
from edalize_common import make_edalize_test


def run_xray_test(tf):
    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    tf.backend.build()
    tf.compare_files(
        ["yosys.cmd", "nextpnr-xilinx.cmd", "fasm2frames.cmd", "xc7frames2bit.cmd"]
    )


def test_xray(make_edalize_test):
    tool_options = {
        "part": "xc7k325t",
        "package": "ffg676-1",
        "yosys_synth_options": ["-abc9", "-flatten"],
        "nextpnr_options": ["--verbose", "--debug"],
    }
    files = [
        {"name": "constraints.xdc", "file_type": "XDC"},
    ]
    tf = make_edalize_test(
        "xray",
        param_types=["vlogdefine", "vlogparam"],
        tool_options=tool_options,
        files=files,
    )

    run_xray_test(tf)
