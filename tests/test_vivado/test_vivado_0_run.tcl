launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

puts "Bitstream generation completed"

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
