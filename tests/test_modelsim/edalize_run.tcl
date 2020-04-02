# Don't exit if a testbench uses $finish so the script
# will continue after run
onfinish stop

proc run_cmd {cmd_list arg_str} {
    set cmd [concat $cmd_list [split $arg_str]]
    eval $cmd
}

set logged_hdl_objs {  "-r /tb/uut/module1"  "/tb/uut/signal1"  }
set logging_enabled [llength $logged_hdl_objs]

if {$logging_enabled} {
    vcd file -dumpports top_module.vcd
    foreach o $logged_hdl_objs {
        run_cmd [list vcd add] $o
    }

    # The power command isn't supported in some versions of ModelSim
    catch { run_cmd [list power add] [lindex $logged_hdl_objs 0]] } pow_cmd

    set power_supported [expr ![string match "Unsupported *: power" $pow_cmd]]

    if {$power_supported} {
        foreach o [lrange $logged_hdl_objs 1 end] {
            run_cmd [list power add] $o
        }
    } else {
        puts "Skipping SAIF recording. Power command not supported in this ModelSim edition"
    }
}

run -all

if {$logging_enabled && $power_supported} {
    power report -all -file top_module_power.txt -bsaif top_module.saif
}

set status [coverage attribute -name TESTSTATUS -concise]

quit -code [expr $status >= 2 ? $status : 0]
