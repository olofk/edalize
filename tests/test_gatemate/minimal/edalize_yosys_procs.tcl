proc read_files {} {

}

proc set_defines {} {
set defines {}

foreach d ${defines} {
  set key [lindex $d 0]
  set val [lindex $d 1]
  verilog_defines "-D$key=$val"
}}

proc set_incdirs {} {
}

proc set_params {} {
}

proc synth {top} {
synth_gatemate  -top $top
}

set top top_module
set name test_gatemate_0
