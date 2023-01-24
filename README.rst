.. image:: https://img.shields.io/readthedocs/edalize?longCache=true&style=flat-square&label=edalize.rtfd.io&logo=ReadTheDocs&logoColor=e8ecef
        :target: https://edalize.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/badge/Chat-on%20gitter-4db797.svg?longCache=true&style=flat-square&logo=gitter&logoColor=e8ecef
   :alt: Join the chat at https://gitter.im/librecores/edalize
   :target: https://gitter.im/librecores/edalize?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

.. image:: https://img.shields.io/pypi/dm/edalize.svg?longCache=true&style=flat-square&logo=PyPI&logoColor=e8ecef&label=PyPI%20downloads
        :target: https://pypi.org/project/edalize/
        :alt: PyPI downloads

.. image:: https://img.shields.io/github/actions/workflow/status/olofk/edalize/ci.yml?branch=main&longCache=true&style=flat-square&label=CI&logo=github%20actions&logoColor=e8ecef
        :target: https://github.com/olofk/edalize/actions/workflows/CI.yml
        :alt: CI status

Edalize
=======

What's this?
------------

Edalize is a Python Library for interacting with EDA tools. It can create project files for supported tools and run them in batch or GUI mode (where supported).

Award-winning `Edalize introduction video`_

All EDA tools such as Icarus, Yosys, ModelSim, Vivado, Verilator, GHDL, Quartus etc get input HDL files (Verilog and VHDL) and some tool-specific files (constraint files, memory initialization files, IP description files etc). Together with the files, perhaps a couple of Verilog \`defines, some top-level parameters/generics or some tool-specific options are set. Once the configuration is done, a simulation model, netlist or FPGA image is built, and in the case of simulations, the model is also executed, maybe with some extra run-time parameters.

The thing is, all these tools are doing this in completely different ways and there's generally no way to import configurations from one simulator to another.

Dread not! Edalize takes care of this for you. By telling Edalize what files you have, together with some info, what parametrization to use at compile- and run-time (e.g. plusargs, defines, generics, parameters), VPI library sources (when applicable) and any other tool-specific options not already mentioned, it will create the necessary project files and offer to build and run it for you.

This will save you from having to deal with the boring stuff of interfacing the EDA tools yourself, while still have pretty much full power to set up the project the way you want.

It allows you to quickly switch tools, at least when it comes to simulators. This is highly useful to shake out tool-specific bugs, or just to let you work with your weapon of choice.

It can also be used to just get a quick template that you can open up in the tool's GUI if there is such, and continue working from there.

It can be directly integrated as a library for your existing Python-powered HDL project, or can be used stand-alone (soon anyway) to feed Edalize from projects written in other languages.

Install it
----------

Edalize is a Python module.
Find the sources at `github.com/olofk/edalize <https://github.com/olofk/edalize>`__.
Once downloaded, we can install it with following Python command::

    $ cd edalize
    $ python -m pip install -e .

The reporting modules have been made optional due to their use of a number of dependencies for data analysis.
These can be installed with::

    $ python -m pip install -e ".[reporting]"

How to use it?
--------------

Ok, this sounds great.
Now, how do I get started?
Find the documentation at `edalize.rtfd.io <https://edalize.rtfd.io>`__.

Assume we have a project that consists of a Verilog source file called ``blinky.v``.
Then there's also a testbench called ``blinky_tb.v`` and a constraints file for synthesis called ``constraints.sdc``.
You can get those files from `blinky <https://github.com/fusesoc/blinky>`_ and for
``vlog_tb_utils.v`` in `orpsoc-cores <https://github.com/fusesoc/vlog_tb_utils/blob/master/vlog_tb_utils.v>`_.

For a simulation, we want to use the two Verilog files, build it in a subdirectory called ``build``, and then run it with a parameter to control simulated clock frequency.

Edalize is a Python tool, then we can run it inside a Python script file or
directly in the Python console.

First we have to import Edalize objects::

  from edalize import *

The os module is also required for this tutorial::

  import os

Then register the files to use::

  work_root = 'build'

  files = [
    {'name' : os.path.relpath('blinky.v', work_root),
     'file_type' : 'verilogSource'},
    {'name' : os.path.relpath('blinky_tb.v', work_root),
     'file_type' : 'verilogSource'},
    {'name' : os.path.relpath('vlog_tb_utils.v', work_root),
     'file_type' : 'verilogSource'}
  ]

The design has a toplevel Verilog parameter with the name ``clk_freq_hz``
that accepts integers. We set its default value to ``1000``. The testbench also
has an option to enable waveform dumping by setting a plusarg called ``vcd``::

  parameters = {'clk_freq_hz' : {'datatype' : 'int', 'default' : 1000, 'paramtype' : 'vlogparam'},
                'vcd' : {'datatype' : 'bool', 'paramtype' : 'plusarg'}}

Let Edalize know we intend to use Icarus Verilog for our simulation::

  tool = 'icarus'

And put it all into a single data structure together with some info about the toplevel and name for the project::

  edam = {
    'files'        : files,
    'name'         : 'blinky_project',
    'parameters'   : parameters,
    'toplevel'     : 'blinky_tb'
  }

Now we need to get ourselves a backend object from Edalize::

  backend = get_edatool(tool)(edam=edam,
                              work_root=work_root)

Create the directory and the project files::

  os.makedirs(work_root)
  backend.configure()

At this point, we still haven't run the actual EDA tool and the files in the ``work_root`` directory can be used without Edalize if that is preferred. But let's continue the example with Edalize.

Build the simulation model::

  backend.build()

And finally run it, with our arguments. Some types of parameters (e.g. plusargs) are defined aat runtime, and at this point we can change their value by passing the name and new value to ``run()``. Or we could skip it altogether, and the default value from the configure stage would be used. Let's run with VCD logging enabled::

  args = {'vcd' : True}
  backend.run(args)

Tada! We have simulated. As an exercise, try to just change the tool variable to e.g. modelsim, xsim or any of the other simulators supported by Edalize and see if it works without any changes.

Now it's time to create an FPGA image instead


As you have seen, Edalize is an award-winning tool for interfacing EDA tools, so

**Edalize it, don't criticize it!**
**Edalize it, and I will advertise it!**

See source code for further details.

.. _`Edalize introduction video`: https://www.youtube.com/watch?v=HuRtkpZqB34
