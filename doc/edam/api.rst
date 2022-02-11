EDA Metadata
============

The EDAM (EDA Metadata) API is a data structure with the intention to describe all input parameters that an EDA tool will need to run synthesis or build a simulation model from a set of HDL files. The data described in EDAM is tool-agnostic, with the option to supply tool-specific parameters when required. The data structure itself is a tree structure with lists and dictionaries using simple data types as strings and integers for the actual values, and is suitable for (de)serialization with YAML or JSON.

Most keys are optional. The ones which are required are marked accordingly

============ ===================== ===========
Field Name   Type                  Description
============ ===================== ===========
files         List of `File`_      Contains all the HDL source files, constraint files,
                                   vendor IP description files, memory initialization files etc. for the project.
hooks         `Hook`_              A dictionary of extra commands to execute at various stages of the project build/run.
name          String               **Required** Name of the project
parameters    Dict of `Parameter`_ Specifies build- and run-time parameters, such as plusargs, VHDL generics, Verilog defines etc.
tool_options  `Tool Options`_      A dictionary of tool-specific options.
toplevel     List of String        Toplevel module(s) for the project.
vpi          List of `VPI`_        VPI modules to build for the project.
============ ===================== ===========


File
----

A file has a name, which is the absolute path or the relative path to the working directory. It also has a type, which describes the intended usage of the file.
Different EDA tools handle different subsets of files and are expected to ignore files that are not applicable to them, but might issue a warning. By specifying *user* as the file type, the backends will explicitly ignore the file. The valid file types are based on the IP-XACT 2014 standard, with some additional file types added. The file types not covered by IP-XACT are listed below

- QIP : Intel Quartus IP file
- UCF : Xilinx ISE constraint file
- verilogSource-2005 : Verilog 200 source
- vhdlSource-2008 : VHDL 2008 source
- xci : Xilinx Vivado IP file
- xdc : Xilinx Vivado constraint file


=============== ===================== ===========
Field Name      Type                  Description
=============== ===================== ===========
name            String                **Required** File name with (absolute or relative) path
file_type       String                **Required** File type
is_include_file Bool                  Indicates if this file should be treated as an include file (default false)
include_path    String                When is_include_file is true, the directory containing the file will be added to the include path. include_path allows setting an explicit directory to use instead
logical_name    String                Logical name (e.g. VHDL/SystemVerilog library) of the file
=============== ===================== ===========

Hook
----

Hooks are scripts that can be registered to execute during various phases of Edalize. The Hook structure contains a key for each of the four defined stages, and the value of each key is a list of Script_ to be executed.

The four defined stages are

=============== =====================
Key             Description
=============== =====================
pre_build       Executed before calling *build*
post_build      Executed after calling *build*
pre_run         Executed before calling *run*
post_run        Executed after calling *run*
=============== =====================

Script
~~~~~~

=============== ===================== ===========
Field Name      Type                  Description
=============== ===================== ===========
cmd             List of String        Command to execute
env             Dict of String        Additional environment variables to set before launching script
name            String                User-friendly name of the script
=============== ===================== ===========


Parameter
---------

A parameter is used for build- and run-time parameters, such as Verilog plusargs, VHDL generics, Verilog defines, Verilog parameters or any extra command-line options that should be sent to the simulation model. Different tools support different subsets of parameters. The list below describes valid parameter types

- cmdlinearg : Command-line argument to be sent to a running simulation model
- generic : VHDL generic to be set at elaboration-time
- plusarg : Verilog plusarg to be set at run-time
- vlogdefine : Verilog define to be set at compile-time
- vlogparam : Verilog toplevel parameter to be set at compile-time

=============== ===================== ===========
Field Name      Type                  Description
=============== ===================== ===========
datatype        String                **Required** Data type of the parameter. Valid values are *bool*, *file*, *int*, *str*.
                                      *file* is similar to *str*, but the value is treated as a path and converted to an absolute path
default         Specified by datatype Default value to use if user does not provide a value during the configure or run stages
description     String                User-friendly description of the parameter
paramtype       String                **Required** Type of parameter. Valid values are *cmdlinearg*, *generic*, *plusarg*, *vlogparam*, *vlogdefine*
=============== ===================== ===========

Tool options
------------

Tool options are used to set tool-specific options. Each key corresponds to a specific EDA tool.

=============== ===================== ===========
Field Name      Type                  Description
=============== ===================== ===========
ghdl            String                Options for GHDL_
icarus          String                Options for Icarus_ Verilog
icestorm        String                Options for Project IceStorm_
ise             String                Options for Xilinx ISE_
isim            String                Options for Xilinx iSim_
modelsim        String                Options for Mentor ModelSim_
openfpga        String                Options for OpenFPGA OpenFPGA_
quartus         String                Options for Intel Quartus_
rivierapro      String                Options for Aldec RivieraPro_
spyglass        String                Options for Synposys SpyGlass_
trellis         String                Options for Project Trellis_
vcs             String                Options for Synopsys VCS_
verilator       String                Options for Verilator_
vivado          String                Options for Xilinx Vivado_
vunit           String                Options for VUnit_
xcelium         String                Options for Cadence Xcelium_
xsim            String                Options for Xilinx XSim_
=============== ===================== ===========

ghdl
~~~~

=============== ===================== ===========
Field Name      Type                  Description
=============== ===================== ===========
analyze_options List of String        Extra options used for the GHDL analyze stage (`ghdl -a`)
run_options     List of String        Extra options used when running GHDL simulations (`ghdl -r`)
=============== ===================== ===========

icarus
~~~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
iverilog_options List of String        Extra options for compilation with `iverilog`
timescale        String                Default (Verilog) timescale to use before user sets one explicitly
================ ===================== ===========

icestorm
~~~~~~~~

=================== ===================== ===========
Field Name          Type                  Description
=================== ===================== ===========
arachne_pnr_options List of String        Options for ArachnePNR Place & Route
nextpnr_options     List of String        Options for NextPNR Place & Route
pnr                 String                Select P&R tool. Valid values are *arachne* and *next*. Default is *arachne*
yosys_synth_options List of String        Options for Yosys Synthesis
=================== ===================== ===========

ise
~~~

================== ===================== ===========
Field Name         Type                  Description
================== ===================== ===========
family             String                FPGA family e.g. *spartan6*, *virtex5*
device             String                Device identifier e.g. *xc6slx45*
package            String                Device package e.g. *csg324*
speed              String                Device speed grade e.g. *-2*
board_device_index String                Specifies the FPGA's device number in the JTAG chain, starting at 1.
================== ===================== ===========

isim
~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
fuse_options     List of String        Extra options for compilation with `fuse`
isim_options     List of String        Extra options for running compiled simulation model
================ ===================== ===========

modelsim
~~~~~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
vlog_options     List of String        Extra options for each Verilog file compiled with `vlog`
vsim_options     List of String        Extra options for running the simulation with `vsim`
================ ===================== ===========

openfpga
~~~~~~~~

The following environment variables need to be sourced before running any simulation on SOFA (**S**\ kywater **O**\ pen-source **F**\ PG\ **A**) IPs:

- ``OPENFPGA_PATH``: directory of the `OpenFPGA framework <https://github.com/lnis-uofu/OpenFPGA>`_ Github repo (`documentation <https://openfpga.readthedocs.io/>`_)
- ``SOFA_PATH``: directory of the `SOFA <https://github.com/lnis-uofu/SOFA>`_ eFPGA IPs Github repo

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
arch             String                FPGA architecture e.g. `sofa-hd`, `sofa-chd`, `sofa-qlhd` and `sofa-plus-hd`
task_options     List of String        Extra options for running the task simulation with OpenFPGA framework (see the OpenFPGA documentation)
================ ===================== ===========


quartus
~~~~~~~

================== ===================== ===========
Field Name         Type                  Description
================== ===================== ===========
board_device_index  List of String        Specifies the FPGA's device number in the JTAG chain. The device index specifies the device where the flash programmer looks for the Nios® II JTAG debug module. JTAG devices are numbered relative to the JTAG chain, starting at 1. Use the tool `jtagconfig` to determine the index.
family              String                FPGA family e.g. *Cyclone IV E*
device              String                Device identifier. e.g. *EP4CE55F23C8* or *5CSXFC6D6F31C8ES*
quartus_options     List of String        Extra command-line options for Quartus
dse_options         List of String        Command-line options for Design Space Explorer
================== ===================== ===========

rivierapro
~~~~~~~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
vlog_options     List of String        Extra options for each Verilog file compiled with `vlog`
vsim_options     List of String        Extra options for running the simulation with `vsim`
================ ===================== ===========

spyglass
~~~~~~~~

=================== ===================== ====================================== ===========
Field Name          Type                  Default                                Description
=================== ===================== ====================================== ===========
methodology         String                ``GuideWare/latest/block/rtl_handoff`` Selected methodology
goals               List of String        ``[ 'lint/lint_rtl' ]``                Selected goals
rule_parameters     List of String        ``[]``                                 Options passed with ``set_option`` to Spyglass, e.g. "handlememory yes" to prevent error SYNTH_5273 on generic RAM descriptions
spyglass_parameters List of String        ``[]``                                 Rule parameters passed with ``set_parameter`` to Spyglass, e.g. ``handle_static_caselabels yes`` to allow localparam to be used in case labels (e.g. in state machines)
=================== ===================== ====================================== ===========

trellis
~~~~~~~

=================== ===================== ===========
Field Name          Type                  Description
=================== ===================== ===========
nextpnr_options     List of String        Options for NextPNR Place & Route
yosys_synth_options List of String        Options for Yosys Synthesis
=================== ===================== ===========

vcs
~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
vcs_options      List of String        Compile time options passed to ``vcs``
run_options      List of String        Runtime options passed to the simulation
================ ===================== ===========

verilator
~~~~~~~~~

================= ===================== ===========
Field Name        Type                  Description
================= ===================== ===========
cli_parser        String                If `cli_parser` is set to managed, Edalize will parse all command-line options.
                                        Otherwise, they are sent directly to the compiled simulation model.
libs              List of String        Extra options to be passed as -LDFLAGS when linking the C++ testbench
mode              String                *cc* runs Verilator in regular C++ mode. *sc* runs in SystemC mode. *lint-only* only performs linting on the Verilog code
verilator_options List of String        Extra options to be passed when verilating model
================= ===================== ===========

vivado
~~~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
part             String                Device identifier. e.g. *xc7a35tcsg324-1*
jobs             Integer               Number of jobs. Useful for parallelizing OOC (Out Of Context) syntheses.
================ ===================== ===========

vunit
~~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
vunit_options    List of String        Extra options for the VUnit test runner
add_libraries    List of String        A list of framework libraries to add. Allowed values include "array_util", "com", "json4hdl", "osvvm", "random", "verification_components"
vunit_runner     String                Name of the Python file exporting a ``VUnitRunner`` class (must derive from ``edalize.vunit_hooks.VUnitHooks``) that is used to configure and execute test. This allows very customized test control via VUnit's Python-interfaces.
================ ===================== ===========

In case a more advanced VUnit configuration or execution of the testbench is necessary, the option ``vunit_runner`` can be used to specify the filename of a Python script which can hook into the construction, parametrization, and execution of the test runner.
For this to work, the Python script must export a ``class VUnitRunner(vunit_hooks.VUnitHooks)`` which derives from (and optionally overrides) the behavior of ``vunit_hooks.VUnitHooks``.

.. code-block:: python

    from edalize.vunit_hooks import VUnitHooks
    from vunit import VUnit
    from vunit.ui import Library, Results
    from typing import Mapping, Collection


    class VUnitRunner(VUnitHooks):
        """Example of custom VUnit instrumentation."""

        def create(self) -> VUnit:
            """Customized creation of the test runner"""
            vu = VUnit.from_argv()
            vu.enable_check_preprocessing()
            return vu

        def handle_library(self, logical_name: str, vu_lib: Library):
            """Override this to customize each library, e.g. with additional simulator options.
            This hook will be invoked for each library, after all source files have been added.
            :param logical_name: The logical name of the library
            :param vu_lib: The vunit.ui.Library instance, configured with all sources of this `logical_name`
            """
            # e.g. you can access and customize test-bench entities of this library:
            if logical_name == "my_tb_library_name":
                entity = vu_lib.entity("my_toplevel_tb")
                entity.set_generic("message", "Test message")
                entity.add_config(name="TestConfig1",
                                generics=dict(CLK_FREQ=10000000))
                entity.add_config(name="TestConfig2",
                                generics=dict(CLK_FREQ=54687500))

        def main(self, vu: VUnit):
            """Override this for final parametrization of the :class:`VUnit` instance (after all libraries have been added),
            or for custom invocation of VUnit
            """
            def post_run_handler(results: Results):
                results.merge_coverage(file_name="coverage_data")

            vu.main(post_run=post_run_handler)


xcelium
~~~~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
xmvlog_options   List of String        Extra options for compilation with `xmvlog`
xmvhdl_options   List of String        Extra options for compilation with `xmvhdl`
xmsim_options    List of String        Extra options for running simulation with with `xsim`
xrun_options     List of String        Extra options for invocation with with `xrun`
================ ===================== ===========

xsim
~~~~

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
xelab_options    List of String        Extra options for compilation with `xelab`
xsim_options     List of String        Extra options for running simulation with with `xsim`
================ ===================== ===========

toplevel
~~~~~~~~
Name of the top level module/entity

VPI
---

Each `Vpi` object contains information on how to build the corresponding VPI library

================ ===================== ===========
Field Name       Type                  Description
================ ===================== ===========
include_dirs     List of String        Extra include directories
libs             List of String        Extra libraries
name             String                Name of VPI library
src_files        List of String        Source files for VPI library
================ ===================== ===========
