vlib work
vcom various vcom_options -quiet -work work vhdl_file.vhd
vlib libx
vcom various vcom_options -quiet -work libx vhdl_lfile
vcom -2008 various vcom_options -quiet -work work vhdl2008_file
vlog some vlog_options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello -sv +incdir+. -quiet -work work -mfcu sv_file.sv vlog_file.v vlog05_file.v another_sv_file.sv