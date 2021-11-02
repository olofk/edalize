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
        'simulator': 'icarus',
        'module': 'python_file',
        'toplevel_lang': 'verilog',
        'random_seed': 1729,
        'testcase': 'test_to_run',
        'cocotb_results_file': 'my_results.xml',
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)

    print(work_root)

    backend.configure()
    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.scr',
    ])

    backend.build()
    compare_files(ref_dir, work_root, ['iverilog.cmd'])

    backend.run()
    compare_files(ref_dir, work_root, ['vvp.cmd'])
