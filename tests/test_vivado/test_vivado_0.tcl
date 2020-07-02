# Auto-generated project tcl file

create_project test_vivado_0 -force

set_property part xc7a35tcsg324-1 [current_project]
#Default since Vivado 2016.1
set_param project.enableVHDL2008 1
set_property generic {vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello } [get_filesets sources_1]
set_property generic {generic_bool=true generic_int=42 generic_str=hello } [get_filesets sources_1]
set_property verilog_define {vlogdefine_bool=1 vlogdefine_int=42 vlogdefine_str=hello } [get_filesets sources_1]
add_files -norecurse qip_file.qip
add_files -norecurse qsys_file
read_xdc -unmanaged sdc_file
add_files -norecurse bmm_file
read_verilog -sv sv_file.sv
add_files -norecurse pcf_file.pcf
add_files -norecurse ucf_file.ucf
source tcl_file.tcl
read_verilog vlog_file.v
read_verilog vlog05_file.v
read_vhdl vhdl_file.vhd
read_vhdl -library libx vhdl_lfile
read_vhdl -vhdl2008 vhdl2008_file
read_ip xci_file.xci
read_xdc xdc_file.xdc
read_mem bootrom.mem
add_files -norecurse c_file.c
add_files -norecurse cpp_file.cpp
add_files -norecurse config.vbl
add_files -norecurse verible_waiver.vbw
add_files -norecurse verible_waiver2.vbw

set_property include_dirs [list . .] [get_filesets sources_1]
set_property top top_module [current_fileset]
set_property source_mgmt_mode None [current_project]
upgrade_ip [get_ips]
generate_target all [get_ips]