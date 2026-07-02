import pytest
from .edalize_flow_common import flow_fixture


def test_gowin(flow_fixture):
    flow_options = {"part": "GW1NR-LV9QN88PC6/I5"}
    ff = flow_fixture("gowin", flow_options=flow_options, paramtypes=[])

    ff.flow.configure()
    ff.compare_config_files(
        [
            "edalize_gowin_template.tcl",
            "Makefile",
        ]
    )


def test_gowin_no_part(flow_fixture):
    flow_options = {}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("gowin", flow_options=flow_options, paramtypes=[])
    assert "FPGA part number must be specified" in str(e.value)


def test_gowin_vlogparam(flow_fixture):
    flow_options = {"part": "GW1NR-LV9QN88PC6/I5"}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("gowin", flow_options=flow_options, paramtypes=["vlogparam"])
    assert "Gowin does not support top level verilog parameters" in str(e.value)
