# This file is generated by Edalize.
# Microsemi Tcl Script
# Libero

source {libero-test-all-project.tcl}

# Source user defined TCL scripts
puts "---------- Executing User pre-synth TCL script: tcl_file_presynth.tcl ----------"
source tcl_file_presynth.tcl
run_tool -name {SYNTHESIZE}

# Source user defined TCL scripts
puts "---------- Executing User pre-pnr TCL script: tcl_file_prepnr.tcl ----------"
source tcl_file_prepnr.tcl
run_tool -name {PLACEROUTE}

# Source user defined TCL scripts
puts "---------- Executing User pre-bitstream TCL script: tcl_file_prebitstream.tcl ----------"
source tcl_file_prebitstream.tcl
run_tool -name {GENERATEPROGRAMMINGDATA}

puts "To program the FPGA and SPI-Flash, run the 'Run PROGRAM Action' and 'Run PROGRAM_SPI_IMAGE Action' tools in the Design Flow menu."
puts "If required, adjust the memory allocation and initialization before generating the bitstream and programming."
puts "----------------- Finished building project -----------------------------"
