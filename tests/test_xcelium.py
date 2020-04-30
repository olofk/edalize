import pytest

def test_xcelium():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_xcelium_0'
    tool         = 'xcelium'
    tool_options = {
        'xmvhdl_options' : ['various', 'xmvhdl_options'],
        'xmvlog_options' : ['some', 'xmvlog_options'],
        'xmsim_options' : ['a', 'few', 'xmsim_options'],
        'xrun_options' : ['plenty', 'of', 'xrun_options'],
    }

    #FIXME: Add VPI tests
    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options, use_vpi=False)
    backend.configure()

    compare_files(ref_dir, work_root, [
        'Makefile',
        'edalize_build_rtl.f',
        'edalize_main.f',
    ])

    orig_env = os.environ.copy()
    os.environ['PATH'] = '{}:{}'.format(os.path.join(tests_dir, 'mock_commands/xcelium'),
                                        os.environ['PATH'])

    # For some strange reason, writing to os.environ['PATH'] doesn't update the environment. This
    # leads to test fails, but only when running multiple tests. When running this test by itself,
    # everything works fine without the 'putenv'.
    os.putenv('PATH', os.environ['PATH'])

    backend.build()
    os.makedirs(os.path.join(work_root, 'work'))

    backend.run()

    compare_files(ref_dir, work_root, ['xrun.cmd'])

    os.environ = orig_env
