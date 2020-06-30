from edalize_common import make_edalize_test


def run_vcs_test(tf):
    tf.backend.configure()

    tf.compare_files(['Makefile', tf.test_name + '.scr'])

    tf.backend.build()
    tf.compare_files(['vcs.cmd'])

    tf.backend.run()
    tf.compare_files(['run.cmd'])


def test_vcs_tool_options(make_edalize_test):
    tool_options = {
        'vcs_options'  : [ '-debug_access+pp', '-debug_access+all' ],
        'run_options'  : [ '-licqueue' ],
    }
    tf = make_edalize_test('vcs',
                           test_name='test_vcs_tool_options_0',
                           ref_dir='tool_options',
                           tool_options=tool_options)
    run_vcs_test(tf)


def test_vcs_no_tool_options(make_edalize_test):
    tf = make_edalize_test('vcs', ref_dir='no_tool_options')
    run_vcs_test(tf)


def test_vcs_minimal(tmpdir):
    import os

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'vcs'
    name = 'test_'+tool+'_minimal_0'
    work_root = str(tmpdir)

    edam = {'name'         : name,
               'toplevel' : 'top'}

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    backend.configure()

    compare_files(ref_dir, work_root, ['Makefile', name + '.scr' ])

    backend.build()
    compare_files(ref_dir, work_root, ['vcs.cmd'])

    backend.run()

    compare_files(ref_dir, work_root, ['run.cmd'])

