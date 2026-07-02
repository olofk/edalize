import pytest
from .edalize_flow_common import flow_fixture


def test_efinity(flow_fixture, monkeypatch):
    monkeypatch.setenv("EFINITY_HOME", "path/to/efinity/intallation")

    flow_options = {"family": "Trion", "part": "T8F81", "timing": "C2"}
    ff = flow_fixture("efinity", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.xml",
            "Makefile",
        ]
    )


def test_efinity_no_env(flow_fixture, monkeypatch):
    monkeypatch.delenv("EFINITY_HOME", raising=False)

    flow_options = {"family": "Trion", "part": "T8F81", "timing": "C2"}
    with pytest.raises(RuntimeError) as e:
        ff = flow_fixture("efinity", flow_options=flow_options)
    assert "The environment variable EFINITY_HOME is not set" in str(e.value)
