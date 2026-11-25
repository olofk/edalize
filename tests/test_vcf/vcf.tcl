# VC Formal Test TCL Script
set_fml_appmode FPV
read_file -top topmodule -format sverilog -sva -vcs "-assert svaext -sverilog sv_file.sv vlog_file.v vlog_with_define.v vlog05_file.v another_sv_file.sv"

create_clock w_clk -period 100
create_clock r_clk -period 150
create_reset w_rst -sense high

sim_config -default_input 0 
sim_run -stable 
sim_force w_rst -apply 1'b0
sim_run -stable 
sim_save_reset 

if ($in_gui_session) { 
    set_fml_var fml_witness_on true
} else {
    check_fv -block
    exit
}