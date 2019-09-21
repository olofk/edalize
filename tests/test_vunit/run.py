
from vunit import VUnit

# Create VUnit instance by parsing command line arguments
vu = VUnit.from_argv()

# Create library 'lib'
lib = vu.add_library("vunit_test_runner")
lib.add_source_files("sv_file.sv")
lib.add_source_files("vlog_file.v")
lib.add_source_files("vlog05_file.v")
lib.add_source_files("vhdl_file.vhd")
lib.add_source_files("vhdl2008_file")
lib = vu.add_library("libx")
lib.add_source_files("vhdl_lfile")

# Run vunit function
vu.main()
