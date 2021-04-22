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

plugin -i xdc
yosys -import
read_xdc -part_json $env(PART_JSON_PATH) $env(XDC_PATH)
clean
write_blif -attr -param $name.eblif

write_blif $name.blif
write_json $name.json
write_edif $name.edif
