# Auto-generated project tcl file


create_project test_vivado_minimal_0 -force

set_property part xc7a35tcsg324-1 [current_project]







set_property include_dirs [list .] [get_filesets sources_1]




# Update marker file for Make. (Run the subsequent jobs only if the marker has been updated)
# This prevents the synthesis from being triggered again if Vivado randomly updates the XPR file's timestamp.
set marker_file [open "test_vivado_minimal_0.xpr.marker" w]
puts $marker_file [clock seconds]
close $marker_file
