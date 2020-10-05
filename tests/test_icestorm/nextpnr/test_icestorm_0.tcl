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
source {tcl_file.tcl}
read_verilog {vlog_file.v}
read_verilog {vlog05_file.v}

chparam -set vlogparam_bool 1 top_module
chparam -set vlogparam_int 42 top_module
chparam -set vlogparam_str {"hello"} top_module
verilog_defaults -pop

synth_ice40 some yosys_synth_options -top top_module
write_blif test_icestorm_0.blif
write_json test_icestorm_0.json
write_edif  test_icestorm_0.edif
