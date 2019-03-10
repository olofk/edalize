all: test_vcs_0

test_vcs_0: test_vcs_0.scr
	vcs -full64 -top top_module -f test_vcs_0.scr -o $@ 
run: test_vcs_0
	./test_vcs_0 -l vcs.log  +plusarg_bool=1  +plusarg_int=42  +plusarg_str=hello 
clean:
	$(RM) test_vcs_0