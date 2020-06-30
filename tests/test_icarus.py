from edalize_common import make_edalize_test


def test_icarus(make_edalize_test):
    name = 'test_icarus_0'
    tool_options = {
        'iverilog_options': ['some', 'iverilog_options'],
        'timescale': '1ns/1ns',
    }
    tf = make_edalize_test('icarus',
                           test_name=name,
                           tool_options=tool_options,
                           use_vpi=True)

    tf.backend.configure()

    tf.compare_files(['Makefile', name + '.scr', 'timescale.v'])

    tf.backend.build()
    tf.compare_files(['iverilog.cmd', 'iverilog-vpi.cmd'])

    tf.backend.run()

    tf.compare_files(['vvp.cmd'])


def test_icarus_minimal(tmpdir):
    import os

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'icarus'
    name = 'test_'+tool+'_minimal_0'
    work_root = str(tmpdir)

    edam = {'name'         : name,
               'toplevel' : 'top'}

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    backend.configure()

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.scr',
    ])

    backend.build()
    compare_files(ref_dir, work_root, ['iverilog.cmd'])

    backend.run()

    compare_files(ref_dir, work_root, ['vvp.cmd'])
