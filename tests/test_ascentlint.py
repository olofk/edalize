import pytest


def test_ascentlint_defaults():
    """ Test the default configuration of Ascent Lint """
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir = os.path.join(tests_dir, __name__, 'defaults')
    paramtypes = ['vlogdefine', 'vlogparam']
    name = 'test_ascentlint'
    tool = 'ascentlint'
    tool_options = {}

    (backend, args, work_root) = setup_backend(
        paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, [
        'Makefile',
        'run-ascentlint.tcl',
        'sources.f',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'ascentlint.cmd',
    ])
