read_edif test_vivado_yosys_0.edif

link_design -top test_vivado_yosys_0 -part xc7a35tcsg324-1


# Vivado will raise an error if impl_1 is launched when it is already done. So
# check the progress first and only launch if its not complete.
if { [get_property PROGRESS [get_runs impl_1]] != "100%"} {
  launch_runs impl_1 -to_step write_bitstream
  wait_on_run impl_1
  puts "Bitstream generation completed"
} else {
  puts "Bitstream generation already complete"
}

report_utilization -file top_utilization_placed.rpt
report_timing_summary -file top_timing_summary_routed.rpt

set vivadoDefaultBitstreamFile [ get_property DIRECTORY [current_run] ]/[ get_property top [current_fileset] ].bit
file copy -force $vivadoDefaultBitstreamFile [pwd]/[current_project].bit
