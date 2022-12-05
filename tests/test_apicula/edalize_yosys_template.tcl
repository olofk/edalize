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

write_json test_apicula_0.json
