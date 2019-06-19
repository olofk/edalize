NAME := test_vivado_minimal_0

all: $(NAME).bit

$(NAME).bit:  $(NAME)_run.tcl $(NAME).xpr
	vivado -mode batch -source $^

$(NAME).xpr: $(NAME).tcl
	vivado -mode batch -source $<

build-gui: $(NAME).xpr
	vivado $<

$(NAME).runs/synth_1: $(NAME)_synth.tcl $(NAME).xpr
	vivado -mode batch -source $^

synth: $(NAME).runs/synth_1
