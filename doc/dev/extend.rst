Extending Edalize
=================

Edalize comes with support for a large number of tools and flows, but there are always more. This section will look at how to add more tools and flows to Edalize, either as contributions to the official Edalize distribution, or as code that can live outside of the Edalize code base. The process for these two alternative ways of extending Edalize is mostly the same, but `Using external tools or flows`_ describes the extra steps for the latter use-case.

Adding a new tool
-----------------

In order to add support for a new EDA tool, a corresponding tool class needs to be defined. A tool class needs to expose which configuration options that are available, together with functions for describing what EDAM output that is created from a given input EDAM description. If there is a need to create any configuration or project files that the EDA tool itself will use, then a function can be defined for that as well. A tool that implemnts the `run` phase (e.g. simulators) also wants to define a function to setup run-time arguments, otherwise that can be left out. These are typically the functions and variables that a tool class wants to implement, but more advanced uses can also fully override the main three phases `configure`, `build` and `run` if needed.

Tool template::

  import os
  from edalize.tools.edatool import Edatool
  from edalize.utils import EdaCommands


  class Customtool(Edatool):

      description = "Custom tool"

      TOOL_OPTIONS = {
          "custom_tool_options": {
              "type": "str",
              "desc": "Additional options for custom tool",
              "list": True,
          },
      }

      def setup(self, edam):
          super().setup(edam)

          used_files = []
          unused_files = []

          for f in self.files:
              # This custom tool only operates on files with file names
              # that have an odd length
              if len(f["name"]) % 2:
                  used_files.append(f["name"])
              else:
                  unused_files.append(f)
          #f"{f['name']} is a {f.get('file_type')} file")

          # Copy the input EDAM and replace the files with the list
          # of unused files + the files that this tool creates
          output_file = self.name + ".count"
          self.edam = edam.copy()
          self.edam["files"] = unused_files
          self.edam["files"].append(
              {
                  "name": output_file,
                  "file_type": "some_kind_of_file",
              }
          )

          # Define a configuration file to be written
          self.config_file = self.name + '.cfg'

	  # Define the command(s) to run the actual EDA tool
	  # This example just uses wc to count the number of
	  # charactes, words and lines of the source files
	  # and writes the results to a file
          commands = EdaCommands()
          commands.add(
              ["wc"]
              + self.tool_options.get("custom_tool_options", [])
              + used_files
              + [self.config_file, ">", output_file],
              [output_file],
              used_files,
          )

	  # Define the default output product of this tool
          commands.set_default_target(output_file)
          self.commands = commands

      def write_config_files(self):
          with open(os.path.join(self.work_root, self.config_file,), "w") as cfg_file:
              cfg_file.write("This is a config file for custom tool\n")

description
  A short text description of the tool.

TOOL_OPTIONS
  A dict of available tool options.

setup(edam)
  A function that is run to create the output EDAM from a given input EDAM.

write_config_files
  A function that is called during the `configure` phase to write out any special configuration files needed by the tool.


Adding a new flow
-----------------

In order to combine existing tools in a new way, a flow class needs to be created. A flow needs to implement the functions, `configure`, `build` and `run` for the three stages of Edalize as well as the `get_tool_options` class function. It also needs the class variable `argtypes` defined.


argtypes
  is a list of parameter types used to indicate which ones that are supported in this flow. The legal values are `cmdlinearg` for command-line arguments, `generic` for VHDL generics, `plusarg` for Verilog plusargs, `vlogparam` for Verilog parameters and `vlogdefine` for Verilog `defines.

get_tool_options(flow_options)
  This function is responsible for returning a dict of all options from all tools in the flow. As the flow options often contain options that affect the flow graph (e.g. `frontends`), this function needs to take the applied set of flow options into consideration when returning the list of tools. The `Edatool` class contains a helper function called `get_filtered_tool_options`that can be used to pick out the right tool options given a list of tools and optionally a dict of options for each tool that has been already defined by the flow and are therefore unavailable to the user.

configure
  The configure function writes out any tool-specific project or configuration files needed as well as the graph execution configuration file (i.e. Makefile).

build
  Calls the previously defined graph execution configuration file to build the default target

run(args)
  For flows that implement the run phase, this is used to call the `run` target in the graph execution configuration file.

Flow template::

  from edalize.flows.edaflow import Edaflow

  class Customexternalflow(Edaflow):

      argtypes = ["plusarg", "vlogdefine", "vlogparam"]

      FLOW_DEFINED_TOOL_OPTIONS = {
          "secondcustomtool": {"some_option": "some_value", "other_option": []},
      }

      @classmethod
      def get_tool_options(cls, flow_options):
        # Add any frontends used in this flow
        flow = flow_options.get("frontends", []).copy()

	# Add the main tool flow
	flow.append("firstcustomtool")
	flow.append("secondcustomtool")
        return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

      def configure(self):
          print("Configuring custom flow")

      def build(self):
          print("Building with custom flow")

      def run(self, args):
          print("Running custom flow")

Many flows can inherit the `configure`, `build` and `run` phases and instead just define functions for configuring the flow and setting the default target, as can be seen in the `generic` flow below.

Generic flow template::

  import os.path
  from importlib import import_module

  from edalize.flows.edaflow import Edaflow, FlowGraph


  class Generic(Edaflow):
      """Run an arbitrary tool"""

      argtypes = ["cmdlinearg", "generic", "plusarg", "vlogdefine", "vlogparam"]

      FLOW_DEFINED_TOOL_OPTIONS = {
      }

      FLOW_OPTIONS = {
          "frontends": {
              "type": "str",
              "desc": "Tools to run before main tool",
              "list": True,
          },
          "tool": {
              "type": "str",
              "desc": "Select tool",
          },
      }

      @classmethod
      def get_tool_options(cls, flow_options):
          flow = flow_options.get("frontends", []).copy()
          tool = flow_options.get("tool")
          if not tool:
              raise RuntimeError("Flow 'generic' requires flow option 'tool' to be set")
          flow.append(tool)

          return cls.get_filtered_tool_options(flow, cls.FLOW_DEFINED_TOOL_OPTIONS)

      def configure_flow(self, flow_options):
          # Check for mandatory flow option "tool"
          tool = self.flow_options.get("tool", "")
          if not tool:
              raise RuntimeError("Flow 'generic' requires flow option 'tool' to be set")

          # Apply flow-defined tool options if any
          fdto = self.FLOW_DEFINED_TOOL_OPTIONS.get(tool, {})

          # Start flow graph dict
          flow = {tool : {"fdto" : fdto}}

          # Apply frontends
          deps = []
          for frontend in flow_options.get("frontends", []):
              flow[frontend] = {"deps" : deps}
              deps = [frontend]

          # Connect frontends to main tool
          flow[tool]["deps"] = deps

          # Create and return flow graph object
          return FlowGraph.fromdict(flow)

      def configure_tools(self, graph):
          super().configure_tools(graph)

          # Set flow default target from the main tool's default target
          tool = self.flow_options.get("tool")

          self.commands.default_target = graph.get_node(tool).inst.commands.default_target

The generic flow can be used to run any single tool class together with a list of frontends. It implements the `configure_flow` and `configure_tools` functions instead of the three main phases.

configure_flow(flow_options)
  This function is used to setup the flow graph. It returns a FlowGraph object that describes which tools to be run and their dependendcies on each other. For convenience, the FlowGraph class contains a function to create a flow graph from a dict where the key is the name of the tool and the value is a dict in itself containing keys to list dependencies (`deps`) and any flow-defined tool options (`fdto`). An example from the `icestorm` flow can be seen here.

  icestorm flow graph as a dict::

    {
        "yosys" : {
            "fdto" : {"arch": "ice40", "output_format": "json"}},
        "nextpnr" : {
            "deps" : ["yosys"],
            "fdto" : {"arch": "ice40"}},
        "icepack" : {
            "deps" : ["nextpnr"]},
        "icetime" : {
            "deps" : ["nextpnr"]},
    }

configure_tools(nodes)
  configure_tools can be used to set the default target of the flow as well as add in any extra commands to be run that are not described in a tool class. This function needs to call configure_tools from the super class first.

Using external tools or flows
-----------------------------

Edalize implements support for implicit namespace packages (https://peps.python.org/pep-0420/) This means that subclasses that logically belong to Edalize can be distributed over several physical locations and is something we can take advantage of to add new flows or tools outside of the Edalize code base.

In order to do that we will create a directory structure that mirrors the structure of Edalize like the example below::

  externalplugin/
      edalize/
          tools/
	      customexternaltool.py
	  flows/
	      customexternalflow.py

The names of the tools and flows are not important and it is possible to have multiple tools or flows in these directories.

There are two common options for making the above `customexternaltool.py` and `customexternalflow.py` available to Edalize.

The first way is to add the `externalplugin` path to ``PYTHONPATH``. The other is to add a `setup.py` in the `externalplugin` directory and install the plugin tools and flows with pip as with other Python packages.

A `setup.py` in its absolutely most minimal form is listed below and is enough to install the plugin as a package in development mode using ``pip install --user -e .`` from the `externalplugin` directory.::

  from setuptools import setup
  setup()

A real `setup.py` like the one used by Edalize normally contains a lot more information.
