import copy
import pytest

def test_cocotb():
    import os
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = []
    name         = 'test_cocotb_0'
    tool         = 'cocotb'
    tool_options = {
        'sim': 'icarus',
        'module': 'python_file',
        'toplevel_lang': 'verilog',
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)

    orig_env = copy.deepcopy(os.environ)
    os.environ['EDALIZE_REF_DIR'] = ref_dir

    backend.configure()
    compare_files(ref_dir, work_root, ['Makefile'])
    backend.build()
    backend.run()
    compare_files(ref_dir, work_root, ['result.txt'])
    
    os.environ = orig_env
