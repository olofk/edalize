EDA Metadata
============

The EDAM (EDA Metadata) API is a data structure with the intention to describe all input parameters that an EDA tool will need to run synthesis or build a simulation model from a set of HDL files. The data described in EDAM is tool-agnostic, with the option to supply tool-specific parameters when required. The data structure itself is a tree structure with lists and dictionaries using simple data types as strings and integers for the actual values, and is suitable for (de)serialization with YAML or JSON.

Most keys are optional. The ones which are required are marked accordingly

============ ===================== ===========
Field Name   Type                  Description
============ ===================== ===========
dependencies Dict of `Dependency`_ Direct dependencies of each core that is contained in the EDAM.
files         List of `File`_      Contains all the HDL source files, constraint files,
                                   vendor IP description files, memory initialization files etc. for the project.
flow_options `Flow Options`_       A dictionary of tool- and flow-specific options. Used by the Flow API
hooks         `Hook`_              A dictionary of extra commands to execute at various stages of the project build/run.
name          String               **Required** Name of the project
parameters    Dict of `Parameter`_ Specifies build- and run-time parameters, such as plusargs, VHDL generics, Verilog defines etc.
tool_options  `Tool Options`_      A dictionary of tool-specific options. Used by the legacy Tool API
toplevel     List of String        Toplevel module(s) for the project.
version      String                EDAM Version of the file.
vpi          List of `VPI`_        VPI modules to build for the project.
============ ===================== ===========

Dependency
----------

An EDAM description is typically composed from multiple cores that have been combined to a larger project. In some cases it can be useful for Edalize flows or tools to be aware of the relation between these cores so that they can recreate the dependency tree. Each Dependency entry contains a list of other cores on which it has a direct dependency.

Example dict of Dependency entries where ::corescore:0 is the toplevel core which depends on ::servant:1.0.0, ::serving:1.0 and ::verilog-axis:0-r2. Both servant and serving in turn depend on serv:

.. code:: yaml

   dependencies:
     ::corescore:0:
     - ::servant:1.0.0
     - ::serving:0
     - ::verilog-axis:0-r2
     ::serv:1.0.0-r1: []
     ::servant:1.0.0:
     - ::serv:1.0.0-r1
     ::serving:0:
     - ::serv:1.0.0-r1
     ::verilog-axis:0-r2: []


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

Flow options
------------

The flow API consists of two layers. The *flow* defines how different *tools* are interconnected to perform a task. The topology of the flows can be very different. A simulation flow might consist of a single simulation tool. An FPGA flow might be built up from a synthesis tool followed by a place & route tool and finally some tool to convert into a device-specific FPGA image (bitstream). A gate-level simulation flow could be created with a synthesis tool feeding its output into a simulator.

This also means that configuring the flow consists of two types of options. The flow options listed for each flow below defines the topology. Depending on which tools that get pulled into the flow graph, additional tool-specific flow options becomes available as well. In addition, some tool-specific options might be hardcoded by the flow. If e.g. yosys is used in the Vivado flow, the architecture will always be set to *xilinx* and the output format will always be *edf* since that's what Vivado expects for its post-synthesis activities. Below is listed the flow options for each flow as well as the tool options for each tool. In order to programatically see what options are available for a specific flow configuration, first run ``get_flow_options()`` to get the available flow options. Assign values to any flow options of interest and then run ``get_tool_options(assigned_flow_options)`` with a dict containing the flow options and their values to see what tool options are available for this particular flow configuration.

The global flow options and options for each tool both goes into the ``flow_options`` section in the EDAM description.

.. include:: flows.rst

.. include:: tools.rst

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

.. include:: legacytools.rst 

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

