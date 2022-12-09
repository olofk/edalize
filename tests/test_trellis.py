import os
import pytest
from .edalize_common import make_edalize_test


def run_trellis_test(tf, pnr_cmdfile="nextpnr-ice40.cmd"):
    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    tf.backend.build()
    tf.compare_files(["yosys.cmd", "nextpnr-ecp5.cmd", "ecppack.cmd"])


def test_trellis(make_edalize_test):
    tool_options = {
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "nextpnr_options": ["a", "few", "nextpnr_options"],
    }
    tf = make_edalize_test(
        "trellis", param_types=["vlogdefine", "vlogparam"], tool_options=tool_options
    )

    run_trellis_test(tf)


def test_trellis_minimal(make_edalize_test):
    tf = make_edalize_test("trellis", param_types=[], files=[], ref_dir="minimal")

    run_trellis_test(tf)


def test_trellis_multiple_pcf(make_edalize_test):
    files = [
        {"name": "pcf_file.pcf", "file_type": "PCF"},
        {"name": "pcf_file2.pcf", "file_type": "PCF"},
    ]
    tf = make_edalize_test("trellis", param_types=[], files=files)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert (
        "Nextpnr only supports one PCF file. Found pcf_file.pcf and pcf_file2.pcf"
        in str(e.value)
    )
