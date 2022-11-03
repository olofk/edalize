TARGET           := test_icarus_minimal_0
TOPLEVEL         := -stop
IVERILOG_OPTIONS := 
VVP_OPTIONS := 

all: $(VPI_MODULES) $(TARGET)

$(TARGET):
	iverilog $(TOPLEVEL) -c $(TARGET).scr -o $@ $(IVERILOG_OPTIONS)

run: $(VPI_MODULES) $(TARGET)
	vvp -n -M. -l icarus.log $(patsubst %.vpi,-m%,$(VPI_MODULES)) $(VVP_OPTIONS) $(TARGET) -fst $(EXTRA_OPTIONS)

clean:
	$(RM) $(VPI_MODULES) $(TARGET)
