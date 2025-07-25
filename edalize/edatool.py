# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
from collections import OrderedDict
from dataclasses import dataclass
from importlib import import_module
import os
import pkgutil


import subprocess
import logging
import sys
from jinja2 import Environment, PackageLoader

logger = logging.getLogger(__name__)

if sys.version[0] == "2":
    FileNotFoundError = OSError
try:
    import msvcrt

    _mswindows = True
except ImportError:
    _mswindows = False

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points, EntryPoint
else:
    from importlib.metadata import entry_points, EntryPoint


NON_TOOL_PACKAGES = [
    "flows",
    "tools",
    "utils",
    "vunit_hooks",
    "reporting",
    "ise_reporting",
    "vivado_reporting",
    "quartus_reporting",
    "version",
]


class ToolResolutionError(RuntimeError):
    pass


@dataclass
class Tool:
    name: str
    tool_class: type

    @property
    def module_path(self) -> str:
        return self.tool_class.__module__

    @property
    def class_name(self) -> str:
        return self.tool_class.__name__


def get_edatool(name: str) -> type:
    if name not in get_edatool_map():
        raise ToolResolutionError(f"Tool {name} not found in edatools.")

    tool_class = get_edatool_map()[name].tool_class

    return tool_class


def get_entrypoint_tool_extensions():
    extension_tools = entry_points(group="edalize.legacy_tool")

    for tool in extension_tools:
        try:
            tool_class = tool.load()
        except ImportError as e:
            raise ToolResolutionError(
                f"Failed to load tool '{tool.name}' from the following registered entrypoint {tool.value}"
            ) from e

        yield Tool(tool.name, tool_class)


def get_namespace_tool_extensions():
    import edalize as namespace_package_to_search

    for mod in pkgutil.iter_modules(
        namespace_package_to_search.__path__, namespace_package_to_search.__name__ + "."
    ):
        tool_name = mod.name.split(".")[1]

        if tool_name not in NON_TOOL_PACKAGES:
            class_name = tool_name.capitalize()

            try:
                tool_module = import_module(mod.name)
            except ImportError as e:
                logger.warning(
                    f"Failed to import namespace extension module {mod.name}, tool {tool_name} is ignored."
                )
                continue

            if not hasattr(tool_module, class_name):
                logger.warning(
                    f"Module {mod.name} found in edalize namespace, but the module does not contain a tool named {tool_name.capitalize()}, tool is ignored."
                )
                continue
            tool_class = getattr(import_module(mod.name), tool_name.capitalize())
            tool = Tool(tool_name, tool_class)
            yield tool


def get_edatool_map():
    tool_map = {tool.name: tool for tool in get_namespace_tool_extensions()}

    entrypoint_tools = {}
    for tool in get_entrypoint_tool_extensions():
        if tool.name in entrypoint_tools:
            # Arguably this should be fatal, but we will just log a warning
            logger.warning(
                f"Tool {tool.name} is defined by multiple entrypoints. Implementation from {tool_map[tool.name].module_path} will be used."
            )
            continue

        if tool.name in tool_map:
            logger.warning(
                f"Tool {tool.name} is defined both in the edalize namespace and as an entrypoint. The entrypoint will take precedence."
            )
        # Track seen entrypoint tools separately to emit duplicate entry diagnostic
        entrypoint_tools[tool.name] = tool

    tool_map.update(entrypoint_tools)

    return tool_map


def get_edatools():
    # Tools from entrypoint will get precedence.
    return [tool.tool_class for tool in get_edatool_map().values()]


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
                "stdout and stderr arguments may not be used with capture_output."
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


if sys.version_info < (3, 8):
    run = subprocess_run_3_9
else:
    run = subprocess.run


# Jinja2 tests and filters, available in all templates
def jinja_filter_param_value_str(value, str_quote_style="", bool_is_str=False):
    """
    Convert a parameter value to string suitable to be passed to an EDA tool.

    Rules:

    - Booleans are represented as 0/1 or "true"/"false" depending on the
      bool_is_str argument
    - Strings are either passed through or enclosed in the characters specified
      in str_quote_style (e.g. '"' or '\\"')
    - Everything else (including int, float, etc.) are converted using the str()
      function.
    """
    if type(value) == bool:
        if bool_is_str:
            return "true" if value else "false"
        else:
            return "1" if value else "0"
    elif type(value) == str:
        return str_quote_style + str(value) + str_quote_style
    else:
        return str(value)


class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = os.path.expandvars(values[0])
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        setattr(namespace, self.dest, [path])


class Edatool(object):
    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        _tool_name = self.__class__.__name__.lower()

        self.verbose = verbose
        self.stdout = None
        self.stderr = None

        if not edam:
            edam = eda_api
        self.edam = edam
        try:
            self.name = edam["name"]
        except KeyError:
            raise RuntimeError("Missing required parameter 'name'")

        self.tool_options = edam.get("tool_options", {}).get(_tool_name, {}).copy()

        self.files = edam.get("files", [])
        self.toplevel = edam.get("toplevel", [])
        self.vpi_modules = edam.get("vpi", [])

        self.hooks = edam.get("hooks", {})
        self.parameters = edam.get("parameters", {})

        self.work_root = work_root
        self.env = os.environ.copy()

        self.env["WORK_ROOT"] = self.work_root

        self.plusarg = OrderedDict()
        self.vlogparam = OrderedDict()
        self.vlogdefine = OrderedDict()
        self.generic = OrderedDict()
        self.cmdlinearg = OrderedDict()

        args = OrderedDict()
        for k, v in self.parameters.items():
            args[k] = v.get("default")
        self._apply_parameters(args)

        # jinja2's PackageLoader needs to know which package to load templates
        # from. This module (edatool.py) belongs to the edalize package but
        # subclass tools using this function might come from other packages
        # through the entrypoint mechanism. We therefore need to look at which
        # module that the class comes form and then load that to see which
        # package it belongs to in order to get the right path for jinja.

        _package = import_module(self.__class__.__module__).__spec__.parent

        self.jinja_env = Environment(
            loader=PackageLoader(_package, "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self.jinja_env.filters["param_value_str"] = jinja_filter_param_value_str
        self.jinja_env.filters["generic_value_str"] = jinja_filter_param_value_str

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            desc = getattr(
                cls, "_description", "Options for {} backend".format(cls.__name__)
            )
            opts = {"description": desc}
            for group in ["members", "lists", "dicts"]:
                if group in cls.tool_options:
                    opts[group] = []
                    for _name, _type in cls.tool_options[group].items():
                        opts[group].append({"name": _name, "type": _type, "desc": ""})
            return opts
        else:
            logger.warning(
                "Invalid API version '{}' for get_tool_options".format(api_ver)
            )

    @classmethod
    def _extend_options(cls, options, other_class):
        help = other_class.get_doc(0)

        options["members"].extend(
            m
            for m in help["members"]
            if m["name"] not in [i["name"] for i in options["members"]]
        )
        options["lists"].extend(
            m
            for m in help["lists"]
            if m["name"] not in [i["name"] for i in options["lists"]]
        )

    def configure(self, args=[]):
        if args:
            logger.error(
                "Edalize has stopped supporting passing arguments as a function argument. Set these values as default values in the EDAM object instead"
            )
        logger.info("Setting up project")
        self.configure_pre()
        self.configure_main()
        self.configure_post()

    def configure_pre(self):
        pass

    def configure_main(self):
        pass

    def configure_post(self):
        pass

    def build(self):
        self.build_pre()
        self.build_main()
        self.build_post()

    def build_pre(self):
        if "pre_build" in self.hooks:
            self._run_scripts(self.hooks["pre_build"], "pre_build")

    def build_main(self, target=None):
        logger.info(
            "Building{}".format("" if target is None else "target " + " ".join(target))
        )
        self._run_tool("make", [] if target is None else [target], quiet=True)

    def build_post(self):
        if "post_build" in self.hooks:
            self._run_scripts(self.hooks["post_build"], "post_build")

    def run(self, args={}):
        logger.info("Running")
        self.run_pre(args)
        self.run_main()
        self.run_post()

    def run_pre(self, args=None):
        if type(args) == list:
            parsed_args = self.parse_args(args, self.argtypes)
        else:
            parsed_args = args
        self._apply_parameters(parsed_args)
        if "pre_run" in self.hooks:
            self._run_scripts(self.hooks["pre_run"], "pre_run")

    def run_main(self):
        pass

    def run_post(self):
        if "post_run" in self.hooks:
            self._run_scripts(self.hooks["post_run"], "post_run")

    def set_default_target(self, target):
        self.default_target = target

    def parse_args(self, args, paramtypes):
        typedict = {
            "bool": {"action": "store_true"},
            "file": {"type": str, "nargs": 1, "action": FileAction},
            "int": {"type": int, "nargs": 1},
            "str": {"type": str, "nargs": 1},
        }
        progname = os.path.basename(sys.argv[0]) + " run {}".format(self.name)

        parser = argparse.ArgumentParser(prog=progname, conflict_handler="resolve")
        param_groups = {}
        _descr = {
            "plusarg": "Verilog plusargs (Run-time option)",
            "vlogparam": "Verilog parameters (Compile-time option)",
            "vlogdefine": "Verilog defines (Compile-time global symbol)",
            "generic": "VHDL generic (Run-time option)",
            "cmdlinearg": "Command-line arguments (Run-time option)",
        }
        param_type_map = {}

        for name, param in self.parameters.items():
            _description = param.get("description", "No description")
            _paramtype = param["paramtype"]
            if _paramtype in paramtypes:
                if not _paramtype in param_groups:
                    param_groups[_paramtype] = parser.add_argument_group(
                        _descr[_paramtype]
                    )

                default = None
                if not param.get("default") is None:
                    try:
                        if param["datatype"] == "bool":
                            default = param["default"]
                        else:
                            default = [
                                typedict[param["datatype"]]["type"](param["default"])
                            ]
                    except KeyError as e:
                        pass
                try:
                    param_groups[_paramtype].add_argument(
                        "--" + name,
                        help=_description,
                        default=default,
                        **typedict[param["datatype"]],
                    )
                except KeyError as e:
                    raise RuntimeError(
                        "Invalid data type {} for parameter '{}'".format(str(e), name)
                    )
                param_type_map[name.replace("-", "_")] = _paramtype
            else:
                logging.warning(
                    "Parameter '{}' has unsupported type '{}' for requested backend".format(
                        name, _paramtype
                    )
                )

        # backend_args.
        backend_args = parser.add_argument_group("Backend arguments")
        _opts = self.__class__.get_doc(0)
        for _opt in _opts.get("members", []) + _opts.get("lists", []):
            backend_args.add_argument("--" + _opt["name"], help=_opt["desc"])

        args_dict = {}
        for key, value in vars(parser.parse_args(args)).items():
            if value is None:
                continue
            if type(value) == list:
                _value = value[0]
            else:
                _value = value
            args_dict[key] = _value
        return args_dict

    def _apply_parameters(self, args):
        _opts = self.__class__.get_doc(0)
        # Parse arguments
        backend_members = [x["name"] for x in _opts.get("members", [])]
        backend_lists = [x["name"] for x in _opts.get("lists", [])]
        for key, value in args.items():
            if value is None:
                continue
            if key in backend_members:
                self.tool_options[key] = value
                continue
            if key in backend_lists:
                if not key in self.tool_options:
                    self.tool_options[key] = []
                self.tool_options[key] += value.split(" ")
                continue

            paramtype = self.parameters[key]["paramtype"]
            getattr(self, paramtype)[key] = value

    def render_template(self, template_file, target_file, template_vars={}):
        """
        Render a Jinja2 template for the backend.

        The template file is expected in the directory templates/BACKEND_NAME.
        """
        template_dir = str(self.__class__.__name__).lower()
        template = self.jinja_env.get_template("/".join([template_dir, template_file]))
        file_path = os.path.join(self.work_root, target_file)
        with open(file_path, "w") as f:
            f.write(template.render(template_vars))

    def _add_include_dir(self, f, incdirs, force_slash=False):
        if f.get("is_include_file"):
            _incdir = f.get("include_path") or os.path.dirname(f["name"]) or "."
            if force_slash:
                _incdir = _incdir.replace("\\", "/")
            if not _incdir in incdirs:
                incdirs.append(_incdir)
            return True
        return False

    def _get_fileset_files(self, force_slash=False):
        class File:
            def __init__(
                self,
                name,
                file_type,
                logical_name,
                core=None,
            ):
                self.name = name
                self.file_type = file_type
                self.logical_name = logical_name
                self.core = core

        incdirs = []
        src_files = []
        for f in self.files:
            if not self._add_include_dir(f, incdirs, force_slash):
                _name = f["name"]
                if force_slash:
                    _name = _name.replace("\\", "/")
                file_type = f.get("file_type", "")
                logical_name = f.get("logical_name", "")
                core = f.get("core", None)
                src_files.append(File(_name, file_type, logical_name, core))
        return (src_files, incdirs)

    def _param_value_str(self, param_value, str_quote_style="", bool_is_str=False):
        return jinja_filter_param_value_str(param_value, str_quote_style, bool_is_str)

    def _run_scripts(self, scripts, hook_name):
        for script in scripts:
            _env = self.env.copy()
            if "env" in script:
                _env.update(script["env"])
            logger.info("Running {} script {}".format(hook_name, script["name"]))
            logger.debug("Environment: " + str(_env))
            logger.debug("Working directory: " + self.work_root)
            try:
                run(
                    script["cmd"],
                    cwd=self.work_root,
                    env=_env,
                    check=True,
                )
            except FileNotFoundError as e:
                msg = "Unable to run {} script '{}': {}"
                raise RuntimeError(msg.format(hook_name, script["name"], str(e)))
            except subprocess.CalledProcessError as e:
                msg = "{} script '{}': {} exited with error code {}".format(
                    hook_name, script["name"], e.cmd, e.returncode
                )
                logger.debug(msg)
                if e.stdout:
                    logger.info(e.stdout.decode())
                if e.stderr:
                    logger.error(e.stderr.decode())
                    logger.debug("=== STDERR ===")
                    logger.debug(e.stderr)
                raise RuntimeError(msg)

    def _run_tool(self, cmd, args=[], quiet=False):
        logger.debug("Running " + cmd)
        logger.debug("args  : " + " ".join(args))

        capture_output = quiet and not (self.verbose or self.stdout or self.stderr)
        try:
            cp = run(
                [cmd] + args,
                cwd=self.work_root,
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

    def _filter_verilog_files(src_file):
        ft = src_file.file_type
        return ft.startswith("verilogSource") or ft.startswith("systemVerilogSource")

    def _write_fileset_to_f_file(
        self, output_file, include_vlogparams=True, filter_func=_filter_verilog_files
    ):
        """
        Write a file list (*.f) file.

        Returns a list of all files which were not added to the *.f file.
        """

        with open(output_file, "w") as f:
            unused_files = []
            (src_files, incdirs) = self._get_fileset_files()

            for key, value in self.vlogdefine.items():
                define_str = self._param_value_str(param_value=value)
                f.write("+define+{}={}\n".format(key, define_str))

            if include_vlogparams:
                for key, value in self.vlogparam.items():
                    param_str = self._param_value_str(
                        param_value=value, str_quote_style='"'
                    )
                    f.write("-pvalue+{}.{}={}\n".format(self.toplevel, key, param_str))

            for id in incdirs:
                f.write("+incdir+" + id + "\n")

            for src_file in src_files:
                if filter_func is None or filter_func(src_file):
                    f.write(src_file.name + "\n")
                else:
                    unused_files.append(src_file)

            return unused_files


def _class_doc(items):
    s = items["description"] + "\n\n"
    lines = []
    name_len = 10
    type_len = 4
    for item in items.get("members", []):
        name_len = max(name_len, len(item["name"]))
        type_len = max(type_len, len(item["type"]))
        lines.append((item["name"], item["type"], item["desc"]))
    for item in items.get("dicts", []):
        name_len = max(name_len, len(item["name"]))
        type_len = max(type_len, len(item["type"]) + 8)
        lines.append((item["name"], "Dict of {}".format(item["type"]), item["desc"]))
    for item in items.get("lists", {}):
        name_len = max(name_len, len(item["name"]))
        type_len = max(type_len, len(item["type"]) + 8)
        lines.append((item["name"], "List of {}".format(item["type"]), item["desc"]))

    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    s += "Field Name".ljust(name_len + 1) + "Type".ljust(type_len + 1) + "Description\n"
    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    for line in lines:
        s += line[0].ljust(name_len + 1)
        s += line[1].ljust(type_len + 1)
        s += line[2]
        s += "\n"
    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    return s


def gen_tool_docs():
    table = []
    s = ""
    for backend in get_edatools():
        name = backend.__name__

        if name == "Edatool":
            continue

        table.append(
            {
                "name": name.lower(),
                "type": "`" + name + " backend`_",
                "desc": name + "-specific options",
            }
        )

        s += "\n{} backend\n{}\n\n".format(name, "~" * (len(name) + 8))
        s += _class_doc(backend.get_doc(0))

    return (
        _class_doc(
            {
                "description": "Tool options are used to set tool-specific options. Each key corresponds to a specific EDA tool.\n\n**Note** This section is only used by the legacy Tool API",
                "members": table,
            }
        )
        + s
    )
