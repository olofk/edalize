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

synth_xilinx  -top []
write_blif test_vivado_yosys_0.blif
write_json test_vivado_yosys_0.json
write_edif -pvector bra test_vivado_yosys_0.edif
