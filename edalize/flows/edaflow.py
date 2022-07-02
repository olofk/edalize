import os
from importlib import import_module

from edalize.utils import EdaCommands

import logging

logger = logging.getLogger(__name__)
import subprocess
import sys


def subprocess_run_3_9(
    *popenargs, input=None, capture_output=False, timeout=None, check=False, **kwargs
):
    if input is not None:
        if kwargs.get("stdin") is not None:
            raise ValueError("stdin and input arguments may not both be used.")
        kwargs["stdin"] = subprocess.PIPE

    if capture_output:
        if kwargs.get("stdout") is not None or kwargs.get("stderr") is not None:
            raise ValueError(
                "stdout and stderr arguments may not be used " "with capture_output."
            )
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    with subprocess.Popen(*popenargs, **kwargs) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except TimeoutExpired as exc:
            process.kill()
            if _mswindows:
                # Windows accumulates the output in a single blocking
                # read() call run on child threads, with the timeout
                # being done in a join() on those threads.  communicate()
                # _after_ kill() is required to collect that and add it
                # to the exception.
                exc.stdout, exc.stderr = process.communicate()
            else:
                # POSIX _communicate already populated the output so
                # far into the TimeoutExpired exception.
                process.wait()
            raise
        except:  # Including KeyboardInterrupt, communicate handled that.
            process.kill()
            # We don't call process.wait() as .__exit__ does that for us.
            raise
        retcode = process.poll()
        if check and retcode:
            raise subprocess.CalledProcessError(
                retcode, process.args, output=stdout, stderr=stderr
            )
    return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)


if sys.version_info < (3, 7):
    run = subprocess_run_3_9
else:
    run = subprocess.run


def merge_dict(d1, d2):
    for key, value in d2.items():
        if isinstance(value, dict):
            d1[key] = merge_dict(d1.get(key, {}), value)
        elif isinstance(value, list):
            d1[key] = d1.get(key, []) + value
        else:
            d1[key] = value
    return d1


class Edaflow(object):

    FLOW = []

    @classmethod
    def get_flow_options(cls):
        flow_opts = cls.FLOW_OPTIONS.copy()
        for tool in cls.FLOW:
            (tool_name, next_nodes, flow_defined_tool_options) = tool

            # Get available tool options from each tool in the flow
            class_tool_options = getattr(
                import_module(f"edalize.tools.{tool_name}"), tool_name.capitalize()
            ).get_tool_options()
            for opt_name in class_tool_options:
                # Filter out tool options that are already set by the flow
                if not opt_name in flow_defined_tool_options:
                    flow_opts[opt_name] = class_tool_options[opt_name]
                    flow_opts[opt_name]["tool"] = tool_name
        return flow_opts

    @classmethod
    def get_tool_options(cls, flow_options):
        return {}

    # Takes a list of tool names and a dict of pre-defined tool options
    # Imports the tool class for every tool in the list, extracts their
    # tool options and return then all, except for the ones listed in
    # flow_defined_tool_options
    @classmethod
    def get_filtered_tool_options(cls, tools, flow_defined_tool_options):
        tool_opts = {}
        for tool_name in tools:

            # Get available tool options from each tool in the list
            try:
                class_tool_options = getattr(
                    import_module(f"edalize.tools.{tool_name}"), tool_name.capitalize()
                ).get_tool_options()
            except ModuleNotFoundError:
                raise RuntimeError(f"Could not find tool '{tool_name}'")
            # Add them to the dict unless they are already set by the flow
            filtered_tool_options = flow_defined_tool_options.get(tool_name, {})
            for opt_name in class_tool_options:
                # Filter out tool options that are already set by the flow
                if not opt_name in filtered_tool_options:
                    tool_opts[opt_name] = class_tool_options[opt_name]
                    tool_opts[opt_name]["tool"] = tool_name

        return tool_opts

    def extract_flow_options(self):
        # Extract flow options from the EDAM
        flow_options = {}
        available_flow_options = [
            k for k, v in self.get_flow_options().items() if not v.get("tool")
        ]
        edam_flow_opts = self.edam.get("flow_options", {})
        for opt_name in list(edam_flow_opts.keys()):
            if opt_name in available_flow_options:  # self.get_flow_options():
                flow_options[opt_name] = edam_flow_opts.pop(opt_name)
        return flow_options

    # Filter out tool options for each tool from self.flow_options
    def extract_tool_options(self):
        tool_options = {}
        edam_flow_opts = self.edam.get("flow_options", {})
        for (tool_name, next_nodes, flow_defined_tool_options) in self.flow:

            # Get the tool class
            ToolClass = getattr(
                import_module(f"edalize.tools.{tool_name}"), tool_name.capitalize()
            )
            # Inject the flow-defined tool options to the EDAM
            tool_options[tool_name] = merge_dict(
                flow_defined_tool_options, tool_options.get(tool_name, {})
            )

            # Assign the EDAM-defined tool options to the right tool
            for opt_name in list(edam_flow_opts.keys()):
                if opt_name in ToolClass.get_tool_options():
                    tool_options[tool_name] = merge_dict(
                        tool_options[tool_name],
                        {opt_name: edam_flow_opts.get(opt_name)},
                    )

            self.edam["tool_options"] = tool_options

    def build_tool_graph(self):
        # Instantiate the tools
        nodes = {}
        for (tool_name, next_nodes, flow_defined_tool_options) in self.flow:

            # Instantiate the tool class
            tool_inst = getattr(
                import_module(f"edalize.tools.{tool_name}"), tool_name.capitalize()
            )()

            # FIXME: Don't like injecting stuff like this
            tool_inst.next_nodes = next_nodes
            tool_inst.work_root = self.work_root

            nodes[tool_name] = tool_inst

        for name, node in nodes.items():
            for next_node in node.next_nodes:
                # Add backwards references
                nodes[next_node].prev_nodes.add(node)
        return nodes

    def configure_tools(self, nodes):
        def merge_edam(a, b):
            # Yeah, I know. It's just a temporary hack
            return b

        unconfigured_nodes = list(nodes.values())
        while unconfigured_nodes:
            node = unconfigured_nodes.pop(0)
            input_edam = {}

            # Check all dependencies are fulfilled
            all_deps_configured = True
            for n in node.prev_nodes:
                if n.edam:
                    input_edam = merge_edam(input_edam, n.edam)
                else:
                    all_deps_configured = False

            if all_deps_configured:
                # No input_edam means this is an input to the flow that should
                # receive the external EDAM.
                if not input_edam:
                    input_edam = self.edam

                node.configure(input_edam)

                # This is an input node. Inject dependency on pre_build scripts
                if not node.prev_nodes:
                    # Inject pre-build scripts before the first command
                    # that the node executes. Note that this isn't
                    # technically correct since the first command in
                    # the list might not be the first command executed
                    node.commands[0].order_only_deps = ["pre_build"]
                self.commands.commands += node.commands

    def add_scripts(self, depends, hook_name):
        last_script = depends
        hooks = self.edam.get("hooks", {})
        for script in hooks.get(hook_name, []):

            # _env = self.env.copy()
            # if 'env' in script:
            #    _env.update(script['env'])

            targets = script["name"]
            command = script["cmd"]
            # FIXME : Add env vars
            self.commands.add(command, [targets], [last_script])

            last_script = script["name"]
        self.commands.add([], [hook_name], [last_script])

    def configure_flow(self, flow_options):
        return self.FLOW

    def __init__(self, edam, work_root, verbose=False):
        self.edam = edam
        self.commands = EdaCommands()

        # Extract all options that affects the flow rather than
        # just a single tool
        self.flow_options = self.extract_flow_options()

        self.flow = self.configure_flow(self.flow_options)

        # Rearrange tool_options so that each tool gets their
        # own tool_options
        self.extract_tool_options()

        self.work_root = work_root

        self.stdout = None
        self.stderr = None

    def set_run_command(self):
        self.commands.add([], ["run"], ["pre_run"])

    def configure(self):

        # Add pre build hooks
        self.add_scripts("", "pre_build")

        # Instantiate all tools (nodes) and build a DAG of the flow
        nodes = self.build_tool_graph()

        # Configure the individual tools in the graph
        self.configure_tools(nodes)

        # Add post_build scripts to the end of the build chain
        self.add_scripts(self.commands.default_target, "post_build")
        self.commands.set_default_target("post_build")

        # Add commands to be executed during the run phase
        self.add_scripts("", "pre_run")
        self.set_run_command()
        self.add_scripts("run", "post_run")

        # Write out execution file
        self.commands.write(os.path.join(self.work_root, "Makefile"))

    def _run_tool(self, cmd, args=[], cwd=None, quiet=False):
        logger.debug("Running " + cmd)
        logger.debug("args  : " + " ".join(args))

        capture_output = quiet and not (self.verbose or self.stdout or self.stderr)
        try:
            cp = run(
                [cmd] + args,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=self.stdout,
                stderr=self.stderr,
                capture_output=capture_output,
                check=True,
            )
        except FileNotFoundError:
            _s = "Command '{}' not found. Make sure it is in $PATH".format(cmd)
            raise RuntimeError(_s)
        except subprocess.CalledProcessError as e:
            _s = "'{}' exited with an error: {}".format(e.cmd, e.returncode)
            logger.debug(_s)

            if e.stdout:
                logger.info(e.stdout.decode())
            if e.stderr:
                logger.error(e.stderr.decode())
                logger.debug("=== STDERR ===")
                logger.debug(e.stderr)

            raise RuntimeError(_s)
        return cp.returncode, cp.stdout, cp.stderr

    def build(self):
        # FIXME: Get run command (e.g. make, ninja, cloud thingie..) from self.commands
        self._run_tool("make", cwd=self.work_root)

    # Most flows won't have a run phase
    def run(self, args):
        pass
