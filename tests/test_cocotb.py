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
        'sim': 'ghdl',
        'module': 'python_file',
        'toplevel_lang': 'vhdl',
        'rtl_library': 'my_lib',
        'gui': 1,
        'waves': 1,
        'compile_args': '--compile-arg',
        'sim_args': '--sim-arg',
        'run_args': '--run-arg',
        'extra_args': '--extra-arg',
        'random_seed': 1729,
        'testcase': 'test_to_run',
        'cocotb_results_file': 'my_results.xml',
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
