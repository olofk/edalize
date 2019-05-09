all: test_vcs_tool_options_0

test_vcs_tool_options_0: test_vcs_tool_options_0.scr
	vcs -full64 -top top_module -f test_vcs_tool_options_0.scr -o $@  -debug_access+pp -debug_access+all
run: test_vcs_tool_options_0
	./test_vcs_tool_options_0 -l vcs.log  +plusarg_bool=1  +plusarg_int=42  +plusarg_str=hello  -licqueue
clean:
	$(RM) test_vcs_tool_options_0
