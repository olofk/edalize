all: test_vcs_minimal_0

test_vcs_minimal_0: test_vcs_minimal_0.scr
	vcs -full64 -top top -f test_vcs_minimal_0.scr -o $@ 
run: test_vcs_minimal_0
	./test_vcs_minimal_0 -l vcs.log 
clean:
	$(RM) test_vcs_minimal_0
