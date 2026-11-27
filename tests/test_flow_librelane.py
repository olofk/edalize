import pytest

from .edalize_flow_common import flow_fixture


def test_librelane(flow_fixture):
    flow_options = {
        "pdk": "gf180mcuD",
        "scl": "gf180mcu_fd_sc_mcu7t5v0",
        "librelane_flow": "Classic",
        "librelane_config": [
            "CLOCK_PORT=clk",
            "CLOCK_PERIOD=20",
            "DIE_AREA=[0, 0, 100, 100]",
        ],
        "librelane_options": ["--dockerized"],
    }
    ff = flow_fixture("librelane", flow_options=flow_options, ref_subdir="options")

    ff.flow.configure()
    ff.compare_config_files(["config.json", "Makefile"])


def test_librelane_minimal(flow_fixture):
    files = [
        {"name": "vlog_file.v", "file_type": "verilogSource"},
        {"name": "/abs/path/sv_file.sv", "file_type": "systemVerilogSource"},
    ]
    ff = flow_fixture("librelane", files=files, ref_subdir="minimal")

    ff.flow.configure()
    ff.compare_config_files(["config.json", "Makefile"])


def test_librelane_multiple_sdc(flow_fixture):
    files = [
        {"name": "a.sdc", "file_type": "SDC"},
        {"name": "b.sdc", "file_type": "SDC"},
    ]
    with pytest.raises(RuntimeError) as e:
        flow_fixture("librelane", files=files)
    assert "LibreLane only supports one SDC file. Found a.sdc and b.sdc" in str(e.value)


def test_librelane_bad_config(flow_fixture):
    flow_options = {"librelane_config": ["CLOCK_PORT"]}
    with pytest.raises(RuntimeError) as e:
        flow_fixture("librelane", flow_options=flow_options)
    assert "librelane_config entry 'CLOCK_PORT' must be on the form KEY=VALUE" in str(
        e.value
    )
