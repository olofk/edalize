import pytest


def do(backend,ref_dir, work_root, files):
    from edalize_common import compare_files
    import os

    for vhdl_file in files :
        with open(os.path.join(work_root, vhdl_file), 'a'):
            os.utime(os.path.join(work_root, vhdl_file), None)

    backend.configure()

    compare_files(ref_dir, work_root, ['Makefile'])

    backend.build()
    compare_files(ref_dir, work_root, ['analyze.cmd'])

    backend.run()
    compare_files(ref_dir, work_root, ['elab-run.cmd'])


LOCAL_FILES = [
      {'name' : 'vhdl_file.vhd', 'file_type' : 'vhdlSource'},
      {'name' : 'vhdl_lfile'   , 'file_type' : 'vhdlSource', 'logical_name' : 'libx'},
]


def test_ghdl_01():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    
    ref_dir      = os.path.join(tests_dir, __name__,"test01")
    paramtypes   = ['generic']
    name         = 'test_ghdl'
    tool         = 'ghdl'
    tool_options = {'analyze_options' : ['some', 'analyze_options'],
                    'run_options'     : ['a', 'few', 'run_options']}

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    

    do(backend,ref_dir,work_root,['vhdl_file.vhd', 'vhdl_lfile',  'vhdl2008_file'])

# Test 02 - no vhdl version specified
def test_ghdl_02():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir    

   
    
    ref_dir =  ref_dir      = os.path.join(tests_dir, __name__,"test02")
    paramtypes   = ['generic']
    name         = 'test_ghdl_02'
    tool         = 'ghdl'
    tool_options = {'analyze_options' : ['some', 'analyze_options'],
                    'run_options'     : ['a', 'few', 'run_options']}

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    # Overload file list with local version
    backend.files = LOCAL_FILES

    do(backend,ref_dir,work_root,['vhdl_file.vhd','vhdl_lfile'])

# Test 03 - vhdl Version override 
def test_ghdl_03():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir    

  
    ref_dir =  ref_dir      = os.path.join(tests_dir, __name__,"test03")
    paramtypes   = ['generic']
    name         = 'test_ghdl_03'
    tool         = 'ghdl'
    tool_options = {'analyze_options' : ['--std=08','--ieee=synopsys'],
                    'run_options'     : ['a', 'few', 'run_options']}

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    # Overload file list with local version
    backend.files = LOCAL_FILES
  
    do(backend,ref_dir,work_root,['vhdl_file.vhd','vhdl_lfile'])    
