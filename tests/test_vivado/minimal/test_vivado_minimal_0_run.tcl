# Create a bin file which can be used to program the flash on the FPGA
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]

# Vivado will raise an error if impl_1 is launched when it is already done. So
# check the progress first and only launch if its not complete.
if { [get_property PROGRESS [get_runs impl_1]] != "100%"} {
  # Vivado only outputs to stdout for jobs that are explicitly waited on with
  # 'wait_on_run'. So launch and wait on synth then launch and wait on impl to
  # get logging to stdout from both.

  launch_runs synth_1 -quiet

  launch_runs impl_1 -to_step write_bitstream
  wait_on_run impl_1
  puts "Bitstream generation completed"
} else {
  puts "Bitstream generation already complete"
}

if { [get_property PROGRESS [get_runs impl_1]] != "100%"} {
   puts "ERROR: Implementation and bitstream generation step failed."
   exit 1
}

# By default, Vivado writes the bitstream to a file named after the toplevel and
# put into the *.runs/impl_1 folder.
# fusesoc/edalize historically used a bitstream name based on the project name,
# and puts it into the top-level project workroot.
# To keep backwards-compat, copy the Vivado default bitstream file to the
# traditional edalize location.
# The Vivado default name is beneficial when using the GUI, as it is set as
# default bitstream in the "Program Device" dialog; non-standard names need to
# be selected from a file picker first.
set vivadoDefaultBitstreamFile [ get_property DIRECTORY [current_run] ]/[ get_property top [current_fileset] ].bit
file copy -force $vivadoDefaultBitstreamFile [pwd]/[current_project].bit
