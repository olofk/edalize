import pytest
from .edalize_flow_common import flow_fixture


def test_icestorm(flow_fixture):
    flow_options = {}
    ff = flow_fixture("icestorm", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_icestorm_pnr_none(flow_fixture):
    flow_options = {"pnr": "none"}
    ff = flow_fixture("icestorm", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )


def test_icestorm_invalid_pnr(flow_fixture):
    flow_options = {"pnr": "foo"}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("icestorm", flow_options=flow_options)
    assert (
        "Invalid pnr option 'foo'. Valid values are 'next' for nextpnr or 'none' to only perform synthesis"
        in str(e.value)
    )
