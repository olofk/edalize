import filecmp
import os
from edalize_common import make_edalize_test, tests_dir


def test_modelsim(make_edalize_test):
    tool_options = {
        'vcom_options': ['various', 'vcom_options'],
        'vlog_options': ['some', 'vlog_options'],
        'vsim_options': ['a', 'few', 'vsim_options'],
    }

    # FIXME: Add VPI tests
    tf = make_edalize_test('modelsim',
                           tool_options=tool_options)

    tf.backend.configure()

    tf.compare_files(['Makefile',
                      'edalize_build_rtl.tcl',
                      'edalize_main.tcl'])

    orig_env = os.environ.copy()
    try:
        os.environ['MODEL_TECH'] = os.path.join(tests_dir, 'mock_commands')

        tf.backend.build()
        os.makedirs(os.path.join(tf.work_root, 'work'))

        tf.compare_files(['vsim.cmd'])

        tf.backend.run()

        assert filecmp.cmp(os.path.join(tf.ref_dir, 'vsim2.cmd'),
                           os.path.join(tf.work_root, 'vsim.cmd'),
                           shallow=False)
    finally:
        os.environ = orig_env
