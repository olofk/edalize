# Auto-generated project tcl file


create_project test_vivado_0 -force

set_property part xc7a35tcsg324-1 [current_project]


set_property generic {vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello } [get_filesets sources_1]
set_property generic {generic_bool=true generic_int=42 generic_str=hello } [get_filesets sources_1]
set_property verilog_define {vlogdefine_bool=1 vlogdefine_int=42 vlogdefine_str=hello } [get_filesets sources_1]
read_edif {netlist.edif}

set_property include_dirs [list .] [get_filesets sources_1]
set_property top top_module [current_fileset]
set_property source_mgmt_mode None [current_project]


