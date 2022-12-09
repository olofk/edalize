import os
import pytest


from .edalize_common import make_edalize_test


def run_mistral_test(tf):

    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    tf.backend.build()
    tf.compare_files(["yosys.cmd", "nextpnr-mistral.cmd"])


def test_mistral(make_edalize_test):
    tool_options = {
        "device": "5CSEBA6U23I7",
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "nextpnr_options": ["a", "few", "nextpnr_options"],
    }

    tf = make_edalize_test(
        "mistral", param_types=["vlogdefine", "vlogparam"], tool_options=tool_options
    )

    run_mistral_test(tf)


def test_mistral_minimal(make_edalize_test):
    tool_options = {
        "device": "5CSEBA6U23I7",
    }

    tf = make_edalize_test(
        "mistral",
        param_types=[],
        files=[],
        tool_options=tool_options,
        ref_dir="minimal",
    )

    run_mistral_test(tf)


def test_mistral_multiple_qsf(make_edalize_test):
    files = [
        {"name": "qsf_file.qsf", "file_type": "QSF"},
        {"name": "qsf_file2.qsf", "file_type": "QSF"},
    ]
    tf = make_edalize_test("mistral", param_types=[], files=files)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert (
        "Nextpnr only supports one QSF file. Found qsf_file.qsf and qsf_file2.qsf"
        in str(e.value)
    )


def test_mistral_no_device(make_edalize_test):
    tf = make_edalize_test("mistral", param_types=[])

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Missing required option 'device' for nextpnr-mistral" in str(e.value)
