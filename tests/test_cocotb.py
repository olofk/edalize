import copy
import pytest
import tempfile

def test_cocotb():
    import os
    from edalize_common import compare_files, _setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    name         = 'test_cocotb_0'
    tool         = 'cocotb'
    paramtypes   = []
    files        = None
    tool_options = {
        'simulator': 'icarus',
        'module': 'python_file',
        'toplevel_lang': 'verilog',
        'random_seed': 1729,
        'testcase': 'test_to_run',
        'cocotb_results_file': 'my_results.xml',
    }
    work_root = tempfile.mkdtemp(prefix=tool+'_')
    toplevel = 'top_module'

    backend = _setup_backend(name, tool, paramtypes, files, tool_options, work_root, False, toplevel)

    backend.configure()
    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.scr',
    ])

    backend.build()
    compare_files(ref_dir, work_root, ['iverilog.cmd'])

    backend.run()
    compare_files(ref_dir, work_root, ['vvp.cmd'])
