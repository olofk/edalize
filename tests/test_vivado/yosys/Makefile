SHELL=/bin/bash
NAME := test_vivado_yosys_0
BITSTREAM := test_vivado_yosys_0.bit
PART := xc7a35tcsg324-1

all: $(BITSTREAM)

$(NAME).edif: $(NAME).mk
	$(MAKE) -f $<

synth: $(NAME).edif

$(BITSTREAM): $(NAME)_run.tcl $(NAME).xpr synth
	$(EDALIZE_LAUNCHER) vivado -notrace -mode batch -source $< $(NAME).xpr

$(NAME).xpr: $(NAME).tcl
	$(EDALIZE_LAUNCHER) vivado -notrace -mode batch -source $<

build-gui: $(NAME).xpr
	$(EDALIZE_LAUNCHER) vivado $<

pgm: $(NAME)_pgm.tcl $(BITSTREAM)
	export HW_TARGET=$(HW_TARGET); \
	export JTAG_FREQ=$(JTAG_FREQ); \
	$(EDALIZE_LAUNCHER) vivado -quiet -nolog -notrace -mode batch -source $< -tclargs $(PART) $(BITSTREAM)
