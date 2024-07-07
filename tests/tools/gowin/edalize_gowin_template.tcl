set_device dummy_part 


add_file -type sdc "sdc_file"
add_file -type verilog "sv_file.sv"
source tcl_file.tcl
add_file -type verilog "vlog_file.v"
add_file -type verilog "vlog_incfile"
add_file -type VHDL_FILE "vhdl_file.vhd"
add_file -type VHDL_FILE "vhdl_lfile"
set_file_prop -lib libx "vhdl_lfile"
add_file -type verilog "another_sv_file.sv"

set_option -top_module top_module
set_option -vhdl_std vhd2008
set_option -verilog_std sysv2017

set_option some
set_option gowin
set_option options


run syn
run pnr