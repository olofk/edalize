set_device GW2AR-LV18QN88C8/I7 


add_file -type sdc "sdc_file"
add_file -type verilog "sv_file.sv"
source tcl_file.tcl
add_file -type verilog "vlog_file.v"
add_file -type verilog "vlog05_file.v"
add_file -type VHDL_FILE "vhdl_file.vhd"
add_file -type VHDL_FILE -library libx "vhdl_lfile"
add_file -type VHDL_FILE "vhdl2008_file"
add_file -type verilog "another_sv_file.sv"


set_option -multi_boot 1

run all