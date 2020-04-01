import pytest

def test_cocotb():
    import os
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_cocotb_0'
    tool         = 'cocotb'
    tool_options = {
        'simulator' : 'modelsim'
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)

    backend.configure()
    compare_files(ref_dir, work_root, ['Makefile'])

    backend.build()
    compare_files(ref_dir, work_root, ['build.txt'])

    backend.run()
    compare_files(ref_dir, work_root, ['run.txt'])
