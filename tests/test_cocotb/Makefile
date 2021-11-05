TARGET           := test_cocotb_0
TOPLEVEL         := top_module
IVERILOG_OPTIONS := 
VPP_OPTIONS := -M /usr/local/lib/python3.9/dist-packages/cocotb/libs -m libcocotbvpi_icarus

all: $(VPI_MODULES) $(TARGET)

$(TARGET):
	iverilog -s$(TOPLEVEL) -c $(TARGET).scr -o $@ $(IVERILOG_OPTIONS)

run: $(VPI_MODULES) $(TARGET)
	vvp -n $(VPP_OPTIONS) -M. -l icarus.log $(patsubst %.vpi,-m%,$(VPI_MODULES)) $(TARGET) -fst $(EXTRA_OPTIONS)

clean:
	$(RM) $(VPI_MODULES) $(TARGET)
