#Generated by Edalize
ifeq (, $(shell which xmroot))
$(error "No Xcelium installation in $(PATH)")
endif

XCELIUM_HOME = $(shell xmroot)

CC ?= gcc
CFLAGS := -c -std=c99 -fPIC -fno-stack-protector -g

LD ?= ld
LDFLAGS := -shared -E

#Only 32 bits is currently supported
CFLAGS  += -m32
LDFLAGS += -melf_i386

RM ?= rm
INCS := -I$(XCELIUM_HOME)/tools/include

XRUN ?= $(XCELIUM_HOME)/tools/bin/xrun

TOPLEVEL      := top_module
DPI_LIBRARIES := -sv_lib libdpi1.so -sv_lib libdpi2.so
PARAMETERS    ?= vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello
PLUSARGS      ?= plusarg_bool=1 plusarg_int=42 plusarg_str=hello
XMSIM_OPTIONS ?= a few xmsim_options
XRUN_OPTIONS  ?= plenty of xrun_options
EXTRA_OPTIONS ?= $(XRUN_OPTIONS) $(DPI_LIBRARIES) $(if $(XMSIM_OPTIONS),-xmsimargs '$(XMSIM_OPTIONS)',) $(addprefix -defparam ,$(PARAMETERS)) $(addprefix +,$(PLUSARGS))

XRUN_CALL = $(XRUN) -q -f edalize_main.f $(EXTRA_OPTIONS) -top $(TOPLEVEL)

all:

run:
	$(XRUN_CALL)

run-gui:
	$(XRUN_CALL) -gui -access rwc
clean:
