import os
import pytest
from .edalize_common import make_edalize_test


def run_gatemate_test(tf):
    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    tf.backend.build()
    tf.compare_files(["yosys.cmd", "p_r.cmd"])


def test_gatemate(make_edalize_test):
    tool_options = {
        "device": "CCGM1A1",
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "p_r_options": ["some", "p_r_synth_options"],
    }
    tf = make_edalize_test(
        "gatemate", param_types=["vlogdefine", "vlogparam"], tool_options=tool_options
    )

    run_gatemate_test(tf)


def test_gatemate_minimal(make_edalize_test):
    tool_options = {
        "device": "CCGM1A1",
    }
    tf = make_edalize_test(
        "gatemate",
        param_types=[],
        files=[],
        tool_options=tool_options,
        ref_dir="minimal",
    )

    run_gatemate_test(tf)


def test_gatemate_multiple_ccf(make_edalize_test):
    files = [
        {"name": "ccf_file.ccf", "file_type": "CCF"},
        {"name": "ccf_file2.ccf", "file_type": "CCF"},
    ]
    tool_options = {
        "device": "CCGM1A1",
    }
    tf = make_edalize_test(
        "gatemate",
        param_types=[],
        files=files,
        tool_options=tool_options,
    )

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert (
        "p_r only supports one ccf file. Found ccf_file.ccf and ccf_file2.ccf"
        in str(e.value)
    )


def test_gatemate_no_device(make_edalize_test):
    tf = make_edalize_test("gatemate", param_types=[])

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Missing required option 'device' for p_r" in str(e.value)


def test_gatemate_wrong_device(make_edalize_test):
    tool_options = {
        "device": "CCGM2A1",
    }

    tf = make_edalize_test("gatemate", param_types=[], tool_options=tool_options)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "CCGM2A1 is not known device name" in str(e.value)


def test_gatemate_wrong_device_size(make_edalize_test):
    tool_options = {
        "device": "CCGM1A13",
    }

    tf = make_edalize_test("gatemate", param_types=[], tool_options=tool_options)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Rel. size 13 is not unsupported" in str(e.value)
