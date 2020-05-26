import pytest


@pytest.mark.parametrize("pnr_tool", ["vtr"])
def test_symbiflow(pnr_tool):
    import os
    import shutil
    import tempfile

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir = os.path.join(tests_dir, __name__, pnr_tool)
    os.environ["PATH"] = (
        os.path.join(tests_dir, "mock_commands") + ":" + os.environ["PATH"]
    )
    tool = "symbiflow"
    tool_options = {
        "part": "xc7a35tcsg324-1",
        "package": "csg324-1",
        "vendor": "xilinx",
        "pnr": pnr_tool,
        "vpr_options": "--fake_option 1000"
    }
    name = "test_vivado_{}_0".format(pnr_tool)
    work_root = tempfile.mkdtemp(prefix=tool + "_")

    files = [{"name": "top.xdc", "file_type": "xdc"}]
    if pnr_tool == "nextpnr":
        files.append({"name": "chipdb.bin", "file_type": "bba"})

    edam = {
        "files": files,
        "name": name,
        "tool_options": {"symbiflow": tool_options},
    }

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    backend.configure()

    config_file_list = [
        "Makefile",
    ]

    if pnr_tool == "nextpnr":
        config_file_list.append(name + ".mk")
        config_file_list.append(name + ".tcl")
        config_file_list.append(name + "-nextpnr.mk")

    compare_files(ref_dir, work_root, config_file_list)
