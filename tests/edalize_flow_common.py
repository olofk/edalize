from importlib import import_module
from pathlib import Path

import pytest
from .edalize_common import compare_files, param_gen, FILES


def get_edam(
    flow_options={},
    paramtypes=["plusarg", "vlogdefine", "vlogparam"],
    name="design",
    files=FILES,
    toplevel="top_module",
):
    parameters = param_gen(paramtypes)
    edam = {
        "name": name,
        "files": files,
        "parameters": parameters,
        "flow_options": flow_options,
        "toplevel": toplevel,
    }
    return edam


def get_flow(name):
    return getattr(import_module("edalize.flows.{}".format(name)), name.capitalize())


class FlowFixture:
    def __init__(self, flow_name, edam, work_root, ref_subdir):
        self.flow = get_flow(flow_name)(edam, work_root)

        self.ref_dir = Path(__file__).parent / "flows" / flow_name / ref_subdir

    def compare_makefile(self):
        compare_files(self.ref_dir, self.flow.work_root, ["Makefile"])

    def compare_config_files(self, config_files):
        compare_files(self.ref_dir, self.flow.work_root, config_files)


@pytest.fixture
def flow_fixture(tmp_path):
    def _flow_fixture(
        flow_name,
        flow_options={},
        files=FILES,
        toplevel="top_module",
        ref_subdir="",
        config_files=[],
    ):

        edam = get_edam(flow_options=flow_options, files=files, toplevel=toplevel)
        ff = FlowFixture(flow_name, edam, tmp_path, ref_subdir)

        # ff.flow.work_root = tmp_path
        # ff.flow.setup(edam)
        # ff.flow.commands.write(tmp_path / "Makefile")
        # ff.compare_makefile()

        return ff

    return _flow_fixture
