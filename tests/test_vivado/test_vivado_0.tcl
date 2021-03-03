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
add_files -norecurse waiver_file.waiver
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
add_files -norecurse config.sby.j2
read_verilog -sv another_sv_file.sv
add_files -norecurse pdc_constraint_file.pdc

set_property include_dirs [list . .] [get_filesets sources_1]
set_property top top_module [current_fileset]
set_property source_mgmt_mode None [current_project]
# Vivado treats IP integrator entities as nested sub-designs and prevents core
# generation from the base project in non-GUI flow raising
# ERROR: [Vivado 12-3563] The Nested sub-design '...xci' can only be generated
#   by its parent sub-design.
# These cores are created and generated separately by Tcl scripts.
# exported from IP integrator. To prevent this error, Ip cores that are part of
# a block design must be excluded from generation at the top level. This can be
# done using `get_ips -filter {SCOPE !~ "*.bd"}`. In Vivado >= 2019.1 the same
# can be achieved using `get_ips -exclude_bd_ips`
upgrade_ip [get_ips -filter {SCOPE !~ "*.bd"}]
generate_target all [get_ips -filter {SCOPE !~ "*.bd"}]