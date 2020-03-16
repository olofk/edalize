import pytest

def test_verilator_cc():
    import os.path
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    mode = 'cc'
    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['cmdlinearg', 'plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_verilator_0'
    tool         = 'verilator'
    tool_options = {
        'libs' : ['-lelf'],
        'mode' : mode,
        'verilator_options' : ['-Wno-fatal', '--trace'],
        'make_options' : ['OPT_FAST=-O2'],
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)

    backend.configure()

    compare_files(ref_dir, work_root, ['Makefile'])

    compare_files(os.path.join(ref_dir, mode),
                  work_root,
                  ['config.mk', name+'.vc'])

    dummy_exe = 'Vtop_module'
    shutil.copy(os.path.join(ref_dir, dummy_exe),
                os.path.join(work_root, dummy_exe))
    backend.run()

    compare_files(ref_dir, work_root, ['run.cmd'])

def test_verilator_sc():
    import os.path
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    mode = 'sc'
    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = []
    name         = 'test_verilator_0'
    tool         = 'verilator'
    tool_options = {
        'mode' : mode,
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)

    backend.configure()

    compare_files(ref_dir, work_root, ['Makefile'])

    compare_files(os.path.join(ref_dir, mode),
                  work_root,
                  ['config.mk', name+'.vc'])

def test_verilator_lint_only():
    import os.path
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    mode = 'lint-only'
    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = []
    name         = 'test_verilator_0'
    tool         = 'verilator'
    tool_options = {
        'mode' : mode,
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)

    backend.configure()

    compare_files(ref_dir, work_root, ['Makefile'])

    compare_files(os.path.join(ref_dir, mode),
                  work_root,
                  ['config.mk', name+'.vc'])
