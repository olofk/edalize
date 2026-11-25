import pytest

from edalize.flows.edaflow import Edaflow

from .edalize_flow_common import flow_fixture

VHDL_FILES = [
    {"name": "top.vhd", "file_type": "vhdlSource-2008"},
    {"name": "tb.v", "file_type": "verilogSource"},
]

VERILOG_FILES = [{"name": "tb.v", "file_type": "verilogSource"}]

PASSING_RESULTS = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites><testsuite name="all"><testcase name="t"/></testsuite></testsuites>
"""


def run_flow(flow_fixture, monkeypatch, tool, files):
    """Build, configure and run the flow, recording the tool invocations.

    cocotb-config is called while the flow is being built, so the tool
    runner has to be replaced before that happens.
    """
    calls = []

    def fake_run_tool(self, cmd, args=[], cwd=None, quiet=False, env={}):
        calls.append({"cmd": cmd, "args": list(args), "env": dict(env)})
        return (0, b"/opt/cocotb/libcocotbvhpi_xcelium.so", b"")

    monkeypatch.setattr(Edaflow, "_run_tool", fake_run_tool)

    ff = flow_fixture(
        "sim",
        flow_options={"tool": tool, "cocotb_module": "some_cocotb_module"},
        files=files,
    )

    ff.flow.configure()
    (ff.flow.work_root / "results.xml").write_text(PASSING_RESULTS)
    ff.flow.run()

    return calls[-1]


def test_cocotb_xcelium_vhdl(flow_fixture, monkeypatch):
    """A VHDL design needs the cocotb VHPI library loading alongside the VPI one."""
    sim = run_flow(flow_fixture, monkeypatch, "xcelium", VHDL_FILES)

    assert sim["env"]["GPI_EXTRA"] == (
        "/opt/cocotb/libcocotbvhpi_xcelium.so:cocotbvhpi_entry_point"
    )
    assert "-NEW_VHPI_PROPAGATE_DELAY" in sim["args"]


def test_cocotb_xcelium_verilog_only(flow_fixture, monkeypatch):
    """A Verilog design is driven through VPI alone, so leave it untouched."""
    sim = run_flow(flow_fixture, monkeypatch, "xcelium", VERILOG_FILES)

    assert "GPI_EXTRA" not in sim["env"]
    assert "-NEW_VHPI_PROPAGATE_DELAY" not in sim["args"]


def test_cocotb_other_simulator_with_vhdl(flow_fixture, monkeypatch):
    """The VHPI arguments are specific to Xcelium."""
    sim = run_flow(flow_fixture, monkeypatch, "ghdl", VHDL_FILES)

    assert "GPI_EXTRA" not in sim["env"]
    assert "-NEW_VHPI_PROPAGATE_DELAY" not in sim["args"]
