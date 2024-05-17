import pytest
from .edalize_flow_common import flow_fixture


def test_sim_no_tool(flow_fixture):
    flow_options = {}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("sim", flow_options=flow_options)
    assert "Flow 'sim' requires flow option 'tool' to be set" in str(e.value)


def test_sim(flow_fixture):
    flow_options = {"tool": "icarus"}
    ff = flow_fixture("sim", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.scr",
            "Makefile",
        ]
    )


def test_sim_cocotb(flow_fixture):
    flow_options = {"tool": "verilator", "cocotb_module": "some_cocotb_module"}
    ff = flow_fixture("sim", flow_options=flow_options, ref_subdir="with_cocotb")

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.vc",
            "Makefile",
        ]
    )
