yosys -import
source edalize_yosys_procs.tcl
load_plugins
yosys -import

verilog_defaults -push
verilog_defaults -add -defer

set_defines
set_incdirs
read_files
set_params

verilog_defaults -pop

synth $top

write_blif $name.blif
