import os
import subprocess
from pathlib import Path

import pytest

from edalize.flows.lint import Lint

from .edalize_flow_common import flow_fixture
from .verible_common import assert_fatality_arguments, assert_fatality_option_types


def test_lint(flow_fixture):
    flow_options = {"tool": "verilator"}
    ff = flow_fixture("lint", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.vc",
            "Makefile",
        ]
    )


def test_lint_verible(flow_fixture):
    tool_options = Lint.get_tool_options({"tool": "verible"})
    assert_fatality_option_types(tool_options)
    assert tool_options["lint_fatal"]["tool"] == "verible"
    assert tool_options["parse_fatal"]["tool"] == "verible"

    flow_case = flow_fixture(
        "lint",
        flow_options={
            "tool": "verible",
            "lint_fatal": False,
            "parse_fatal": True,
        },
        ref_subdir="verible",
    )

    assert flow_case.flow.edam["tool_options"]["verible"] == {
        "lint_fatal": False,
        "parse_fatal": True,
    }

    flow_case.flow.configure()
    flow_case.compare_config_files(["Makefile"])

    makefile = (Path(flow_case.flow.work_root) / "Makefile").read_text()
    assert_fatality_arguments(makefile, {"lint_fatal": False, "parse_fatal": True})


def test_lint_verible_rebuilds_changed_inputs_with_lint_directory(
    flow_fixture, monkeypatch
):
    mock_commands = Path(__file__).parent / "mock_commands"
    monkeypatch.setenv("PATH", f"{mock_commands}{os.pathsep}{os.environ['PATH']}")

    files = [
        {"name": "top.sv", "file_type": "systemVerilogSource"},
        {"name": "lint/rules.cfg", "file_type": "veribleLintRules"},
        {"name": "lint/waivers.cfg", "file_type": "veribleLintWaiver"},
        {
            "name": "defs.svh",
            "file_type": "systemVerilogSource",
            "is_include_file": True,
        },
    ]
    flow_case = flow_fixture("lint", flow_options={"tool": "verible"}, files=files)
    work_root = Path(flow_case.flow.work_root)
    (work_root / "top.sv").touch()
    (work_root / "lint").mkdir()
    (work_root / "lint" / "rules.cfg").touch()
    (work_root / "lint" / "waivers.cfg").touch()
    (work_root / "defs.svh").touch()

    flow_case.flow.configure()
    makefile = (work_root / "Makefile").read_text()
    assert "design.verible.done:" in makefile

    flow_case.flow.build()
    flow_case.flow.build()

    invocations = (work_root / "verible-verilog-lint.cmd").read_text().splitlines()
    assert len(invocations) == 1

    inputs = ("top.sv", "defs.svh", "lint/rules.cfg", "lint/waivers.cfg", "Makefile")
    for filename in inputs:
        stamp = work_root / "design.verible.done"
        # Only the selected input is newer than the stamp. Use fixed times
        # to avoid sleeps and filesystem timestamp-resolution assumptions.
        for input_file in inputs:
            os.utime(work_root / input_file, (1, 1))
        os.utime(stamp, (2, 2))
        os.utime(work_root / filename, (3, 3))
        flow_case.flow.build()
    assert len(
        (work_root / "verible-verilog-lint.cmd").read_text().splitlines()
    ) == 1 + len(inputs)


@pytest.mark.parametrize("lint_fails", [False, True])
def test_verible_frontend_orders_simulation_build(
    flow_fixture, monkeypatch, lint_fails
):
    flow_case = flow_fixture(
        "sim",
        flow_options={"tool": "icarus", "frontends": ["verible"]},
        files=[{"name": "top.sv", "file_type": "systemVerilogSource"}],
    )
    work_root = Path(flow_case.flow.work_root)
    (work_root / "top.sv").write_text("module top; endmodule\n")
    bin_dir = work_root / "bin"
    bin_dir.mkdir()
    linter = bin_dir / "verible-verilog-lint"
    linter.write_text(
        "#!/bin/sh\necho lint >> events\nexit " + str(int(lint_fails)) + "\n"
    )
    compiler = bin_dir / "iverilog"
    compiler.write_text(
        "#!/bin/sh\n"
        "test -f design.verible.done || exit 1\n"
        "grep -qx top.sv design.scr || exit 1\n"
        "echo compile >> events\ntouch design\n"
    )
    for executable in (linter, compiler):
        executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    flow_case.flow.configure()
    result = subprocess.run(["make", "-j4"], cwd=work_root, capture_output=True)
    assert (result.returncode != 0) == lint_fails, result.stderr.decode()
    assert (work_root / "events").read_text().splitlines() == (
        ["lint"] if lint_fails else ["lint", "compile"]
    )
    assert (work_root / "design.verible.done").exists() != lint_fails
    if not lint_fails:
        subprocess.run(["make", "-j4"], cwd=work_root, check=True, capture_output=True)
        assert (work_root / "events").read_text().splitlines() == ["lint", "compile"]
