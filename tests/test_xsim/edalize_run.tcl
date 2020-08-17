proc run_cmd {cmd_list arg_str} {
    set cmd [concat $cmd_list [split $arg_str]]
    eval $cmd
}

set logged_hdl_objs {  "-r /tb/uut/m1"  "/tb/uut/signal1"  }
set logging_enabled [llength $logged_hdl_objs]

if {$logging_enabled} {

    open_vcd top_module.vcd
    open_saif top_module.saif

    foreach o $logged_hdl_objs {
        set objects [run_cmd [list get_objects] $o]
        log_vcd $objects
        log_saif $objects
    }
}

run -all

if {$logging_enabled} {
    flush_vcd
    close_vcd
    close_saif
}

quit
