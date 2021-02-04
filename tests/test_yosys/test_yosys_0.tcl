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
read_verilog -sv {another_sv_file.sv}

chparam -set vlogparam_bool 1 top_module
chparam -set vlogparam_int 42 top_module
chparam -set vlogparam_str {"hello"} top_module
verilog_defaults -pop

synth  -top top_module
dfflibmap -liberty /some/path/to/your/tech.lib
abc -liberty /some/path/to/your/tech.lib
clean
stat -top top_module -liberty /some/path/to/your/tech.lib
write_blif test_yosys_0.blif
write_json test_yosys_0.json
write_edif  test_yosys_0.edif
write_verilog test_yosys_0.v
