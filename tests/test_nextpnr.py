import pytest

def test_nextpnr():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['generic', 'vlogdefine', 'vlogparam']
    name         = 'test_nextpnr'
    tool         = 'nextpnr'
    tool_options = {
        'part' : 'xc7a35tcsg324-1',
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure()

    compare_files(ref_dir, work_root, [
        'Makefile',
        name+'.tcl',
        name+'.mk',
    ])
