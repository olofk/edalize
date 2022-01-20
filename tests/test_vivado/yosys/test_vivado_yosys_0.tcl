# Auto-generated project tcl file


create_project test_vivado_yosys_0 -force

set_property part xc7a35tcsg324-1 [current_project]





read_edif {test_vivado_yosys_0.edif}

set_property include_dirs [list .] [get_filesets sources_1]



link_design -top test_vivado_yosys_0 -part xc7a35tcsg324-1