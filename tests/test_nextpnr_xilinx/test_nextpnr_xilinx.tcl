yosys -import

set defines {{vlogdefine_bool True} {vlogdefine_int 42} {vlogdefine_str hello}}

foreach d ${defines} {
  set key [lindex $d 0]
  set val [lindex $d 1]
  verilog_defines "-D$key=$val"
}
verilog_defaults -push
verilog_defaults -add -defer

verilog_defaults -add -I.
read_verilog -sv {sv_file.sv}
read_verilog {vlog_file.v}

chparam -set vlogparam_bool 1 top_module
chparam -set vlogparam_int 42 top_module
chparam -set vlogparam_str {"hello"} top_module
verilog_defaults -pop

synth_xilinx  -top top_module
write_blif test_nextpnr_xilinx.blif
write_json test_nextpnr_xilinx.json
write_edif -pvector bra test_nextpnr_xilinx.edif
