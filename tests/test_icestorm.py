import os
import pytest
from .edalize_common import make_edalize_test


def run_icestorm_test(tf, pnr_cmdfile="nextpnr-ice40.cmd"):
    tf.backend.configure()

    tf.compare_files(
        ["Makefile", "edalize_yosys_procs.tcl", "edalize_yosys_template.tcl"]
    )

    for x in [
        "pcf_file.pcf",
        "sv_file.sv",
        "tcl_file.tcl",
        "vlog_file.v",
        "vlog05_file.v",
        "vlog_incfile",
        "another_sv_file.sv",
    ]:
        f = os.path.join(tf.work_root, x)
        with open(f, "a"):
            os.utime(f, None)

    tf.backend.build()
    tf.compare_files(["yosys.cmd", pnr_cmdfile, "icepack.cmd"])


def test_icestorm(make_edalize_test):
    tool_options = {
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "arachne_pnr_options": ["a", "few", "arachne_pnr_options"],
    }
    tf = make_edalize_test(
        "icestorm", param_types=["vlogdefine", "vlogparam"], tool_options=tool_options
    )

    run_icestorm_test(tf)


def test_icestorm_minimal(make_edalize_test):
    files = [{"name": "pcf_file.pcf", "file_type": "PCF"}]
    tf = make_edalize_test("icestorm", param_types=[], files=files, ref_dir="minimal")

    run_icestorm_test(tf)


def test_icestorm_no_pcf(make_edalize_test):
    tf = make_edalize_test("icestorm", param_types=[], files=[])

    tf.backend.configure()


def test_icestorm_multiple_pcf(make_edalize_test):
    files = [
        {"name": "pcf_file.pcf", "file_type": "PCF"},
        {"name": "pcf_file2.pcf", "file_type": "PCF"},
    ]

    with pytest.raises(RuntimeError) as e:
        tf = make_edalize_test("icestorm", param_types=[], files=files)
    assert (
        "Nextpnr only supports one PCF file. Found pcf_file.pcf and pcf_file2.pcf"
        in str(e.value)
    )


def test_icestorm_nextpnr(make_edalize_test):
    tool_options = {
        "yosys_synth_options": ["some", "yosys_synth_options"],
        "arachne_pnr_options": ["a", "few", "arachne_pnr_options"],
        "nextpnr_options": ["multiple", "nextpnr_options"],
        "icepack_options": ["several", "icepack_options"],
        "pnr": "next",
    }
    tf = make_edalize_test(
        "icestorm",
        param_types=["vlogdefine", "vlogparam"],
        tool_options=tool_options,
        ref_dir="nextpnr",
    )

    run_icestorm_test(tf, pnr_cmdfile="nextpnr-ice40.cmd")


def test_icestorm_invalid_pnr(make_edalize_test):
    name = "test_icestorm_0"

    with pytest.raises(RuntimeError) as e:
        tf = make_edalize_test(
            "icestorm",
            test_name=name,
            param_types=["vlogdefine", "vlogparam"],
            tool_options={"pnr": "invalid"},
            ref_dir="nextpnr",
        )
    assert (
        "Invalid pnr option 'invalid'. Valid values are 'next' for nextpnr or 'none' to only perform synthesis"
        in str(e.value)
    )
