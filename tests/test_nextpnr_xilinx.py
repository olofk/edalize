import pytest

def test_nextpnr():
    import os
    import shutil
    import tempfile

    from edalize import get_edatool
    from edalize_common import compare_files, tests_dir, param_gen

    ref_dir = os.path.join(tests_dir, __name__)
    os.environ["PATH"] = (
        os.path.join(tests_dir, "mock_commands") + ":" + os.environ["PATH"]
    )
    tool = "nextpnr_xilinx"
    parameters = param_gen(["vlogparam", "vlogdefine"])
    name = "test_{}".format(tool)
    work_root = tempfile.mkdtemp(prefix=tool + "_")

    files = [{"name": "xdc_file.xdc", "file_type": "xdc"}, {"name": "chipdb.bin", "file_type": "chipDataBase"}, {"name": ".", "file_type": "verilog", 'is_include_file': 'true'},{"name": "sv_file.sv", "file_type": "systemVerilogSource"},{"name": "vlog_file.v", "file_type": "verilogSource"}]

    edam = {
        "files": files,
        "name": name,
        'toplevel': 'top_module',
        "parameters": parameters,
        "incdirs" : ".",
    }

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    backend.configure()

    config_file_list = [
        "Makefile",
        name + ".mk",
        name + ".tcl",
    ]

    compare_files(ref_dir, work_root, config_file_list)
