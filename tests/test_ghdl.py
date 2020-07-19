import os
from edalize_common import make_edalize_test



def test_ghdl_01(make_edalize_test):
    tf = make_edalize_test('ghdl',
                           ref_dir = "test01",
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



LOCAL_FILES = [
      {'name' : 'vhdl_file.vhd', 'file_type' : 'vhdlSource'},
      {'name' : 'vhdl_lfile'   , 'file_type' : 'vhdlSource', 'logical_name' : 'libx'},
]

# Test 02 - no vhdl version specified
def test_ghdl_02(make_edalize_test):
    tf = make_edalize_test('ghdl',
                           ref_dir = "test02",
                           test_name = "test_ghdl_02",
                           param_types=['generic'],
                           files = LOCAL_FILES,
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



# Test 03 - vhdl Version override
def test_ghdl_03(make_edalize_test):
    tf = make_edalize_test('ghdl',
                           ref_dir = "test03",
                           test_name = "test_ghdl_03",
                           param_types=['generic'],
                           files = LOCAL_FILES,
                           tool_options={
                               'analyze_options': ['--std=08','--ieee=synopsys'],
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