vlib work
vlog +incdir+. a few vlog options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello -sv -quiet -work work sv_file.sv
vlog +incdir+. a few vlog options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello -quiet -work work vlog_file.v
vlog +incdir+. a few vlog options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello -quiet -work work vlog05_file.v
vcom several vcom options -quiet -work work vhdl_file.vhd
vlib libx
vcom several vcom options -quiet -work libx vhdl_lfile
vcom -2008 several vcom options -quiet -work work vhdl2008_file
vlog +incdir+. a few vlog options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello -sv -quiet -work work another_sv_file.sv