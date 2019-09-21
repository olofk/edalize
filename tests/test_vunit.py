import pytest
import os.path
from edalize_common import compare_files, setup_backend, tests_dir


def test_vunit():
    ref_dir = os.path.join(tests_dir, __name__)
    paramtypes = ['cmdlinearg']
    name = 'test_vunit_0'
    tool = 'vunit'
    tool_options = {}

    (backend, args, work_root) = setup_backend(
        paramtypes, name, tool, tool_options, use_vpi=False)

    backend.configure(args)
    compare_files(ref_dir, work_root, [
        'run.py'
    ])
