SHELL=/bin/bash
NAME := test_vivado_yosys_0
BITSTREAM := test_vivado_yosys_0.bit
PART := xc7z010clg400-1

all: $(BITSTREAM)
$(NAME).edif: $(NAME).mk
	$(MAKE) -f $<
$(BITSTREAM): $(NAME)_run.tcl $(NAME).xpr synth
	vivado -notrace -mode batch -source $< $(NAME).xpr

$(NAME).xpr: $(NAME).tcl synth
	vivado -notrace -mode batch -source $(NAME).tcl


build-gui: $(NAME).xpr
	vivado $<

$(NAME).runs/synth_1/top.dcp: $(NAME)_synth.tcl $(NAME).xpr
	vivado -notrace -mode batch -source $^

synth: $(NAME).edif


pgm: $(NAME)_pgm.tcl $(BITSTREAM)
	export HW_TARGET=$(HW_TARGET); \
	export JTAG_FREQ=$(JTAG_FREQ); \
	vivado -quiet -nolog -notrace -mode batch -source $< -tclargs $(PART) $(BITSTREAM)

.PHONY: pgm
