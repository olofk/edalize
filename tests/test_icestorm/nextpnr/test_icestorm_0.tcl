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
set file_table {{sv_file.sv -sv} {vlog_file.v }}

foreach f ${file_table} {
  set file_path [lindex $f 0]
  set opts ""
  if {[llength $f] == 2} {
    set opts [lindex $f 1]
  }

  # Yosys does not like empty $opt variables
  if {$opts eq ""} {
    read_verilog $file_path
  } else {
    read_verilog $opts $file_path
  }
}

chparam -set vlogparam_bool 1 \$abstract\top_module
chparam -set vlogparam_int 42 \$abstract\top_module
chparam -set vlogparam_str {"hello"} \$abstract\top_module
verilog_defaults -pop

synth_ice40 some yosys_synth_options -top top_module
write_blif test_icestorm_0.blif
write_json test_icestorm_0.json
