Edalize
=======

What's this?
------------

Edalize is a Python Library for interacting with EDA tools. It can create project files for supported tools and run them in batch or GUI mode (where supported).

All EDA tools such as Icarus, Yosys, ModelSim, Vivado, Verilator, GHDL, Quartus etc get input HDL files (verilog and VHDL) and some tool-specific files (constraint files, memory initialization files, IP description files etc). Together with the files, perhaps a couple of verilog \`defines, some top-level parameters/generics or some tool-specific options are set. Once the configuration is done, a simulation model, netlist or FPGA image is built, and in the case of simulations, the model is also executed, maybe with some extra run-time parameters.

The thing is, all these tools are doing this in completely different ways and there's generally no way to import configurations from one simulator to another.

Dread not! Edalize takes care of this for you. By telling Edalize what files you have, together with some info, what parametrization to use at compile- and run-time (e.g. plusargs, defines, generics, parameters), VPI library sources (when applicable) and any other tool-specific options not already mentioned, it will create the necessary project files and offer to build and run it for you.

This will save you from having to deal with the boring stuff of interfacing the EDA tools yourself, while still have pretty much full power to set up the project the way you want.

It allows you to quickly switch tools, at least when it comes to simulators. This is highly useful to shake out tool-specific bugs, or just to let you work with your weapon of choice.

It can also be used to just get a quick template that you can open up in the tool's GUI if there is such, and continue working from there.

It can be directly integrated as a library for your existing Python-powered HDL project, or can be used stand-alone (soon anyway) to feed Edalize from projects written in other languages.

How to use it?
--------------

Ok, this sounds great. Now, how do I get started?

Assume we have a project that consists of a verilog source file called blinky.v. Then there's also a testbench called blinky_tb.v and a constraints file for synthesis called constraints.sdc. You can get those files from here https://github.com/fusesoc/blinky

For a simulation, we want to use the two verilog files, build it in a subdirectory called "build", and then run it with a parameter to control simulated clock frequency.

First we register the files to use::

  work_root = 'build'

  files = [
    {'name' : os.path.relpath('blinky.v', work_root),
     'file_type' : 'verilogSource'},
    {'name' : os.path.relpath('blinky_tb.v', work_root),
     'file_type' : 'verilogSource'}
  ]


Then we have our parameter, with the the name clk_freq_hz and happens to be a verilog parameter that accepts integers::

  parameters = {'clk_freq_hz' : {'datatype' : 'int', 'paramtype' : 'vlogparam'}}

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

  args = ['--clk_freq_hz=1000']
  os.makedirs(work_root)
  backend.configure(args)
  
At this point, we still haven't run the actual EDA tool and the files in the work_root directory can be used without edalize if that is preferred. But let's continue the example with Edalize.

Build the simulation model::
  
  backend.build()

And finally run it, with our arguments. At this point we could change the value of clk_freq_hz, and the new value would be used instead. Or we could skip it altogether, and the default value from the configure stage would be used.::

  backend.run(args)

Tada! We have simulated. As an exercise, try to just change the tool variable to e.g. modelsim, xsim or any of the other simulators supported by Edalize and see if it works without any changes.

Now it's time to create an FPGA image instead


As you have seen, Edalize is an award-winning tool for interfacing EDA tools, so

**Edalize it, don't criticize it!**
**Edalize it, and I will advertise it!**

See source code for further details.
