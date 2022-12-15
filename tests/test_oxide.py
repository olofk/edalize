import os
import pytest
from .edalize_common import make_edalize_test


def run_oxide_test(tf):
    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    tf.backend.build()
    tf.compare_files(["yosys.cmd", "nextpnr-nexus.cmd", "prjoxide.cmd"])


def test_oxide(make_edalize_test):
    tool_options = {
        "device": "LIFCL-40-9BG400CES",
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "nextpnr_options": ["a", "few", "nextpnr_options"],
    }
    tf = make_edalize_test(
        "oxide", param_types=["vlogdefine", "vlogparam"], tool_options=tool_options
    )

    run_oxide_test(tf)


def test_oxide_minimal(make_edalize_test):
    tool_options = {
        "device": "LIFCL-40-9BG400CES",
    }
    tf = make_edalize_test(
        "oxide", param_types=[], files=[], tool_options=tool_options, ref_dir="minimal"
    )

    run_oxide_test(tf)


def test_oxide_multiple_pdc(make_edalize_test):
    files = [
        {"name": "pdc_file.pdc", "file_type": "PDC"},
        {"name": "pdc_file2.pdc", "file_type": "PDC"},
    ]
    tf = make_edalize_test("oxide", param_types=[], files=files)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert (
        "Nextpnr only supports one PDC file. Found pdc_file.pdc and pdc_file2.pdc"
        in str(e.value)
    )


def test_oxide_no_device(make_edalize_test):
    tf = make_edalize_test("oxide", param_types=[])

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Missing required option 'device' for nextpnr-nexus" in str(e.value)
