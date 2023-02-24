# Auto-generated project tcl file


create_project design -force



#Default since Vivado 2016.1
set_param project.enableVHDL2008 1
set_property generic {vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello } [get_filesets sources_1]

set_property verilog_define {vlogdefine_bool=1 vlogdefine_int=42 vlogdefine_str=hello } [get_filesets sources_1]
read_xdc -unmanaged {sdc_file}
read_verilog -sv {sv_file.sv}
source {tcl_file.tcl}
read_verilog {vlog_file.v}
read_verilog {vlog05_file.v}
read_vhdl {vhdl_file.vhd}
read_vhdl -library libx {vhdl_lfile}
read_vhdl -vhdl2008 {vhdl2008_file}
read_ip {xci_file.xci}
read_xdc {xdc_file.xdc}
read_mem {bootrom.mem}
read_verilog -sv {another_sv_file.sv}

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
