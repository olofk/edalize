from importlib import import_module
from pathlib import Path

import pytest
from .edalize_common import compare_files, param_gen, FILES


def get_edam(
    tool_name,
    tool_options={},
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
        "tool_options": {tool_name: tool_options},
        "toplevel": toplevel,
    }
    return edam


def get_tool(name):
    return getattr(import_module("edalize.tools.{}".format(name)), name.capitalize())


class ToolFixture:
    def __init__(self, tool_name, ref_subdir):
        self.tool = get_tool(tool_name)()

        self.ref_dir = Path(__file__).parent / "tools" / tool_name / ref_subdir

    def compare_makefile(self):
        compare_files(self.ref_dir, self.tool.work_root, ["Makefile"])

    def compare_config_files(self, config_files):
        compare_files(self.ref_dir, self.tool.work_root, config_files)


@pytest.fixture
def tool_fixture(tmp_path):
    def _tool_fixture(
        tool_name,
        tool_options={},
        files=FILES,
        toplevel="top_module",
        ref_subdir="",
        config_files=[],
    ):

        tf = ToolFixture(tool_name, ref_subdir)

        edam = get_edam(
            tool_name, tool_options=tool_options, files=files, toplevel=toplevel
        )

        tf.tool.work_root = tmp_path
        tf.tool.setup(edam)
        tf.tool.commands.write(tmp_path / "Makefile")
        tf.compare_makefile()

        return tf

    return _tool_fixture
