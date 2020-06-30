import os
from edalize_common import make_edalize_test


def test_ghdl(make_edalize_test):
    tf = make_edalize_test('ghdl',
                           param_types=['generic'],
                           tool_options={
                               'analyze_options': ['some', 'analyze_options'],
                               'run_options': ['a', 'few', 'run_options']
                           })

    for vhdl_file in ['vhdl_file.vhd', 'vhdl_lfile',  'vhdl2008_file']:
        with open(os.path.join(tf.work_root, vhdl_file), 'a'):
            os.utime(os.path.join(tf.work_root, vhdl_file), None)

    tf.backend.configure()

    tf.compare_files(['Makefile'])

    tf.backend.build()
    tf.compare_files(['analyze.cmd'])

    tf.backend.run()
    tf.compare_files(['elab-run.cmd'])
