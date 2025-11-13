import logging
import pytest
from .edalize_flow_common import flow_fixture

logger = logging.getLogger(__name__)


def test_apicula_no_device(flow_fixture):
    flow_options = {}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="error")
    assert "Missing required option 'device' for apicula" in str(e.value)


def test_apicula_devices(flow_fixture):
    # Tang Nano
    flow_options = {"device": "GW1N-LV1QN48C6/I5"}
    flow_fixture("apicula", flow_options=flow_options, ref_subdir="success")
    # Tang Nano 9k
    flow_options = {"device": "GW1NR-LV9QN88PC6/I5", "device_family": "C"}
    flow_fixture("apicula", flow_options=flow_options, ref_subdir="success")

    flow_options = {"device": "GW3NR-LV9Q"}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="error")
    assert "Unknown device GW3NR-LV9Q" in str(e.value)

    flow_options = {"device": "GW1NR-LV9QN88PC6/I5", "device_family": "Q"}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="error")
    assert "Unknown device family code Q" in str(e.value)

    # Tang Nano 20k
    flow_options = {"device": "GW2AR-LV18QN88C8/I7", "device_family": "C"}
    flow_fixture("apicula", flow_options=flow_options, ref_subdir="success")
    # Tang Primer 25k
    flow_options = {"device": "GW5A-LV25MG121NES"}
    flow_fixture("apicula", flow_options=flow_options, ref_subdir="success")


def test_apicula_boards(flow_fixture):
    flow_options = {"board": "apa"}
    with pytest.raises(RuntimeError) as e:
        flow_fixture("apicula", flow_options=flow_options, ref_subdir="tangprimer25k")
    assert "Missing required option 'device' for apicula" in str(e.value)


def test_apicula_board_tangnano(flow_fixture):
    logger.warning("tangnano")
    # Tang Nano
    flow_options = {"board": "tangnano"}
    ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="tangnano")
    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_apicula_board_tangnano9k(flow_fixture):
    logger.warning("tangnano9k")
    # Tang Nano 9k
    flow_options = {"board": "tangnano9k"}
    ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="tangnano9k")
    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_apicula_board_tangnano20k(flow_fixture):
    logger.warning("tangnano20k")
    # Tang Nano 20k
    flow_options = {"board": "tangnano20k"}
    ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="tangnano20k")
    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_apicula(flow_fixture):
    logger.warning("tangnano9k - numbers")
    flow_options = {
        "board": "tangnano9k",
        "device": "GW1NR-LV9QN88PC6/I5",
        "device_family": "C",
    }
    ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="tangnano9k")
    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_apicula_no_family(flow_fixture):
    logger.warning("tangnano - numbers")
    flow_options = {"board": "tangnano", "device": "GW1N-LV1QN48C6/I5"}
    ff = flow_fixture("apicula", flow_options=flow_options, ref_subdir="tangnano")
    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_apicula_board_override_device(flow_fixture):
    logger.warning("tangnano - numbers")
    flow_options = {
        "board": "tangnano",
        "device": "GW1NR-LV9QN88PC6/I5",
        "device_family": "C",
    }
    ff = flow_fixture(
        "apicula", flow_options=flow_options, ref_subdir="tangnano-override"
    )
    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )
