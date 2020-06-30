from edalize_common import make_edalize_test


def test_diamond(make_edalize_test):
    name = 'test_diamond_0'
    tf = make_edalize_test('diamond',
                           test_name=name,
                           param_types=['generic', 'vlogdefine', 'vlogparam'],
                           tool_options={
                               'part': 'LFE5U-85F-6BG381C',
                           })

    tf.backend.configure()

    tf.compare_files([name + '.tcl', name + '_run.tcl'])

    tf.backend.build()

    tf.compare_files(['diamondc.cmd'])


def test_diamond_minimal(tmpdir):
    import os

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'diamond'
    tool_options = {
        'part' : 'LFE5U-85F-6BG381C',
    }
    name = 'test_{}_minimal_0'.format(tool)
    work_root = str(tmpdir)

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
