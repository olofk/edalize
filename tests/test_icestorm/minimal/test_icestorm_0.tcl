yosys -import

set defines {}

foreach d ${defines} {
  set key [lindex $d 0]
  set val [lindex $d 1]
  verilog_defines "-D$key=$val"
}
verilog_defaults -push
verilog_defaults -add -defer





verilog_defaults -pop

synth_ice40  -top top_module
write_blif test_icestorm_0.blif
write_json test_icestorm_0.json
write_edif  test_icestorm_0.edif
