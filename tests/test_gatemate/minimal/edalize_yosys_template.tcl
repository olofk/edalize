yosys -import
source edalize_yosys_procs.tcl

verilog_defaults -push
verilog_defaults -add -defer

set_defines
set_incdirs
read_files
set_params

verilog_defaults -pop

synth $top

write_verilog test_gatemate_0_synth.v
