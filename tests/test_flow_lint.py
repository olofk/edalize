import os
from pathlib import Path

from edalize.flows.lint import Lint

from .edalize_flow_common import flow_fixture


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
    assert tool_options["lint_fatal"]["type"] == "bool"
    assert tool_options["lint_fatal"]["tool"] == "verible"
    assert tool_options["parse_fatal"]["type"] == "bool"
    assert tool_options["parse_fatal"]["tool"] == "verible"

    ff = flow_fixture(
        "lint",
        flow_options={
            "tool": "verible",
            "lint_fatal": False,
            "parse_fatal": True,
        },
        ref_subdir="verible",
    )

    assert ff.flow.edam["tool_options"]["verible"] == {
        "lint_fatal": False,
        "parse_fatal": True,
    }

    ff.flow.configure()
    ff.compare_config_files(["Makefile"])

    makefile = (Path(ff.flow.work_root) / "Makefile").read_text()
    assert makefile.count("--lint_fatal=false") == 1
    assert makefile.count("--parse_fatal=true") == 1


def test_lint_verible_runs_repeatedly_with_lint_directory(flow_fixture, monkeypatch):
    mock_commands = Path(__file__).parent / "mock_commands"
    monkeypatch.setenv("PATH", f"{mock_commands}{os.pathsep}{os.environ['PATH']}")

    files = [
        {"name": "top.sv", "file_type": "systemVerilogSource"},
        {"name": "lint/rules.cfg", "file_type": "veribleLintRules"},
    ]
    ff = flow_fixture("lint", flow_options={"tool": "verible"}, files=files)
    work_root = Path(ff.flow.work_root)
    (work_root / "top.sv").touch()
    (work_root / "lint").mkdir()
    (work_root / "lint" / "rules.cfg").touch()

    ff.flow.configure()
    makefile = (work_root / "Makefile").read_text()
    assert ".PHONY: lint" in makefile

    ff.flow.build()
    ff.flow.build()

    invocations = (work_root / "verible-verilog-lint.cmd").read_text().splitlines()
    assert len(invocations) == 2
