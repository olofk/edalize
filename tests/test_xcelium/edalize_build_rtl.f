-makelib worklib some xmvlog_options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello -sv +incdir+. sv_file.sv -endlib
-makelib worklib some xmvlog_options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello +incdir+. vlog_file.v -endlib
-makelib worklib some xmvlog_options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello +incdir+. vlog05_file.v -endlib
-makelib worklib various xmvhdl_options vhdl_file.vhd -endlib
-makelib libx various xmvhdl_options vhdl_lfile -endlib
-makelib worklib -v200x various xmvhdl_options vhdl2008_file -endlib
