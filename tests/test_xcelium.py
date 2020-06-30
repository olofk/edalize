import os
from edalize_common import make_edalize_test, tests_dir


def test_xcelium(make_edalize_test):
    tool_options = {
        'xmvhdl_options' : ['various', 'xmvhdl_options'],
        'xmvlog_options' : ['some', 'xmvlog_options'],
        'xmsim_options' : ['a', 'few', 'xmsim_options'],
        'xrun_options' : ['plenty', 'of', 'xrun_options'],
    }

    #FIXME: Add VPI tests
    tf = make_edalize_test('xcelium', tool_options=tool_options)

    tf.backend.configure()
    tf.compare_files(['Makefile',
                      'edalize_build_rtl.f',
                      'edalize_main.f'])

    orig_env = os.environ.copy()
    try:
        os.environ['PATH'] = '{}:{}'.format(os.path.join(tests_dir, 'mock_commands/xcelium'),
                                            os.environ['PATH'])

        # For some strange reason, writing to os.environ['PATH'] doesn't update the environment. This
        # leads to test fails, but only when running multiple tests. When running this test by itself,
        # everything works fine without the 'putenv'.
        os.putenv('PATH', os.environ['PATH'])

        tf.backend.build()
        os.makedirs(os.path.join(tf.work_root, 'work'))

        tf.backend.run()
        tf.compare_files(['xrun.cmd'])
    finally:
        os.environ = orig_env
