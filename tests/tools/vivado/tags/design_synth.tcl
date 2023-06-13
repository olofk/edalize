set outdated [get_property NEEDS_REFRESH [get_runs synth_1]]
set progress [get_property PROGRESS [get_runs synth_1]]

if {$outdated || $progress != "100%"} {
    reset_runs synth_1
    launch_runs synth_1
    wait_on_run synth_1
}
#exit [regexp -nocase -- {synth_design (error|failed)} [get_property STATUS [get_runs synth_1]] match]
