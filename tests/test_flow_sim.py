import pytest

from edalize.flows.sim import Sim


def test_sim_no_tool(flow_fixture):
    flow_options = {}
    with pytest.raises(RuntimeError) as e:
        flow_fixture("sim", flow_options=flow_options)
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


@pytest.mark.parametrize(
    "has_entry_point,user_gpi_users,expected",
    [
        (True, None, "/libpython.so;/pygpi.so,initialize"),
        (False, None, None),
        (True, "user", None),
    ],
)
def test_sim_cocotb_gpi_users(
    flow_fixture, monkeypatch, has_entry_point, user_gpi_users, expected
):
    outputs = {
        "--libpython": b"/libpython.so\n",
        "--python-bin": b"/python\n",
        "--help": b"--pygpi-entry-point" if has_entry_point else b"",
        "--pygpi-entry-point": b"/pygpi.so,initialize\n",
    }
    envs = []

    def run_tool(self, cmd, args=[], cwd=None, quiet=False, env={}):
        if cmd == "cocotb-config":
            return 0, outputs[args[0]], b""
        envs.append(env)
        return 0, b"", b""

    monkeypatch.setattr(Sim, "_run_tool", run_tool)
    monkeypatch.setattr(Sim, "_check_junit_xml", lambda self, file: None)
    monkeypatch.delenv("GPI_USERS", raising=False)
    if user_gpi_users:
        monkeypatch.setenv("GPI_USERS", user_gpi_users)

    flow_options = {"tool": "verilator", "cocotb_module": "some_cocotb_module"}
    ff = flow_fixture("sim", flow_options=flow_options)
    ff.flow.configure()
    ff.flow.run()

    assert envs[0].get("GPI_USERS") == expected
    assert envs[0]["MODULE"] == "some_cocotb_module"
