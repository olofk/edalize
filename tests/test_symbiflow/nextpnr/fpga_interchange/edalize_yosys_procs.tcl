proc read_files {} {

}

proc set_defines {} {
set defines {{vlogdefine_bool True} {vlogdefine_int 42} {vlogdefine_str hello}}

foreach d ${defines} {
  set key [lindex $d 0]
  set val [lindex $d 1]
  verilog_defines "-D$key=$val"
}}

proc set_incdirs {} {
}

proc set_params {} {
chparam -set vlogparam_bool 1 top_module
chparam -set vlogparam_int 42 top_module
chparam -set vlogparam_str {"hello"} top_module}

proc synth {top} {
synth_xilinx  -top $top
}

set top top_module
set name test_symbiflow_nextpnr_fpga_interchange_0
