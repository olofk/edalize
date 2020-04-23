import pytest

def test_diamond():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['generic', 'vlogdefine', 'vlogparam']
    tool         = 'diamond'
    name         = 'test_{}_0'.format(tool)
    tool_options = {
        'part' : 'LFE5U-85F-6BG381C',
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure()

    compare_files(ref_dir, work_root, [
        name+'.tcl',
        name+'_run.tcl',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'diamondc.cmd',
    ])

def test_diamond_minimal():
    import os
    import shutil
    import tempfile

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'diamond'
    tool_options = {
        'part' : 'LFE5U-85F-6BG381C',
    }
    name = 'test_{}_minimal_0'.format(tool)
    work_root = tempfile.mkdtemp(prefix=tool+'_')

    edam = {'name'         : name,
            'tool_options' : {tool : tool_options}
    }

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    backend.configure()

    compare_files(ref_dir, work_root, [
        name+'.tcl',
        name+'_run.tcl',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'diamondc.cmd',
    ])
