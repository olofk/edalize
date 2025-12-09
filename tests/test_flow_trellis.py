import pytest
from .edalize_flow_common import flow_fixture


def test_trellis(flow_fixture):
    flow_options = {}
    ff = flow_fixture("trellis", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )
