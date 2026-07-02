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



# Update marker file for Make. (Run the subsequent jobs only if the marker has been updated)
# This prevents the synthesis from being triggered again if Vivado randomly updates the XPR file's timestamp.
set marker_file [open "test_vivado_0.xpr.marker" w]
puts $marker_file [clock seconds]
close $marker_file
