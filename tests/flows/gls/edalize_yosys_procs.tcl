proc load_plugins {} {
}

proc read_files {} {
read_verilog -sv {sv_file.sv}
source {tcl_file.tcl}
read_verilog {vlog_file.v}
read_verilog {vlog05_file.v}
read_verilog -sv {another_sv_file.sv}
}

proc set_defines {} {
set defines {{vlogdefine_bool True} {vlogdefine_int 42} {vlogdefine_str hello}}

foreach d ${defines} {
  set key [lindex $d 0]
  set val [lindex $d 1]
  verilog_defines "-D$key=$val"
}}

proc set_incdirs {} {
verilog_defaults -add -I.}

proc set_params {} {
chparam -set vlogparam_bool 1 None
chparam -set vlogparam_int 42 None
chparam -set vlogparam_str {"hello"} None}

proc synth {top} {
synth_ice40  -top $top
}

set top None
set name design
