import pytest


def test_veribleformat_default():
    """ Test the format mode of Verible """
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir = os.path.join(tests_dir, __name__, 'default')
    paramtypes = ['vlogdefine', 'vlogparam']
    name = 'test_verible'
    tool = 'veribleformat'
    tool_options = {}

    (backend, work_root) = setup_backend(
        paramtypes, name, tool, tool_options)
    backend.configure()
    backend.build()
    backend.run()
    compare_files(ref_dir, work_root, [
        'verilog_format.cmd',
    ])
