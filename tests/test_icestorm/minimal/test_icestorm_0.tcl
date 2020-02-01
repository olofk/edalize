yosys -import

set defines {}

foreach d ${defines} {
  set key [lindex $d 0]
  set val [lindex $d 1]
  verilog_defines "-D$key=$val"
}
verilog_defaults -push
verilog_defaults -add -defer


set file_table {}

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


verilog_defaults -pop

synth_ice40  -top top_module
write_blif test_icestorm_0.blif
write_json test_icestorm_0.json
