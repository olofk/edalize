import os
import pytest
from .edalize_common import make_edalize_test


def run_apicula_test(tf):
    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    tf.backend.build()
    tf.compare_files(["yosys.cmd", "nextpnr-gowin.cmd", "gowin_pack.cmd"])


def test_apicula(make_edalize_test):
    tool_options = {
        "device": "GW1N-LV1QN48C6/I5",
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "nextpnr_options": ["a", "few", "nextpnr_options"],
    }
    tf = make_edalize_test(
        "apicula", param_types=["vlogdefine", "vlogparam"], tool_options=tool_options
    )

    run_apicula_test(tf)


def test_apicula_minimal(make_edalize_test):
    tool_options = {
        "device": "GW1N-LV1QN48C6/I5",
    }
    tf = make_edalize_test(
        "apicula",
        param_types=[],
        files=[],
        tool_options=tool_options,
        ref_dir="minimal",
    )

    run_apicula_test(tf)


def test_apicula_multiple_cst(make_edalize_test):
    files = [
        {"name": "cst_file.cst", "file_type": "CST"},
        {"name": "cst_file2.cst", "file_type": "CST"},
    ]
    tf = make_edalize_test("apicula", param_types=[], files=files)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert (
        "Nextpnr only supports one CST file. Found cst_file.cst and cst_file2.cst"
        in str(e.value)
    )


def test_apicula_no_device(make_edalize_test):
    tf = make_edalize_test("apicula", param_types=[])

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Missing required option 'device' for nextpnr-gowin" in str(e.value)
