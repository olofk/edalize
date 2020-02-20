Reports from untested builds of the [PicoRV32 RISCV
CPU](https://github.com/cliffordwolf/picorv32) for several tools and devices.

A wrapper of some form is needed since this design uses far more pins than
provided by these devices. The Quartus builds used `VIRTUAL_PIN` constraints
from the [virtual_pins
generator](https://github.com/fusesoc/fusesoc-generators). The Xilinx builds
used the wrapped version of the core from the [SymbiFlow FPGA tool performance
profiling project](https://github.com/SymbiFlow/fpga-tool-perf/).

There are [reported problems with ISE synthesis and this
design](https://github.com/cliffordwolf/picorv32/issues/38) so this run is
potentially suspect, but produced the right report files.

