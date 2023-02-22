# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
from jinja2 import Environment, PackageLoader
from edalize.utils import EdaCommands

# Jinja2 tests and filters, available in all templates
def jinja_filter_param_value_str(value, str_quote_style="", bool_is_str=False):
    """Convert a parameter value to string suitable to be passed to an EDA tool

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


class Edatool(object):
    TOOL_OPTIONS = {}

    @classmethod
    def get_tool_options(cls):
        return cls.TOOL_OPTIONS

    def __init__(self):
        self.edam = None
        self.prev_nodes = set()
        self.jinja_env = Environment(
            loader=PackageLoader(__package__, "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self.jinja_env.filters["param_value_str"] = jinja_filter_param_value_str
        self.jinja_env.filters["generic_value_str"] = jinja_filter_param_value_str

    def _require_tool_option(self, option_name):
        option = self.tool_options.get(option_name)
        if not option:
            raise RuntimeError(
                f"{self.__class__.__name__.lower()} requires tool option '{option_name}'"
            )
        return option

    def setup(self, edam):
        self.edam = edam
        try:
            self.name = edam["name"]
        except KeyError:
            raise RuntimeError("Missing required parameter 'name'")

        _tool_name = self.__class__.__name__.lower()

        self.tool_options = edam.get("tool_options", {}).get(_tool_name, {})

        self.files = edam.get("files", [])
        self.toplevel = edam.get("toplevel", [])
        self.vpi_modules = edam.get("vpi", [])

        self.hooks = edam.get("hooks", {})
        self.parameters = edam.get("parameters", {})

        self.plusarg = {}
        self.vlogparam = {}
        self.vlogdefine = {}
        self.generic = {}
        self.cmdlinearg = {}

        args = {}
        for k, v in self.parameters.items():
            args[k] = v.get("default")
        self._apply_parameters(args)

    def configure(self):
        self.write_config_files()

    # Subclasses implement this. Called at the end of configure
    def write_config_files(self):
        pass

    def update_config_file(self, file_name, contents):
        """
        Check contents against the file file_name in work_root.
        If these differ or file_name doesn't exist,
        write contents to file_name
        """
        f = os.path.join(self.work_root, file_name)
        if os.path.exists(f):
            old_file = open(f, "r").read()
        else:
            old_file = ""
        if old_file != contents:
            with open(f, "w") as _f:
                _f.write(contents)

    def set_default_target(self, target):
        self.default_target = target

    def _apply_parameters(self, args):
        for key, value in args.items():
            # Ignore parameters without value
            if value is None:
                pass
            # If the parameter is a tool option we handle it elsewhere
            elif key in self.get_tool_options():
                pass
            # Otherwise it's design parameter that is handled here
            else:
                paramtype = self.parameters[key]["paramtype"]
                getattr(self, paramtype)[key] = value

    def render_template(self, template_file, target_file, template_vars={}):
        """
        Render a Jinja2 template for the backend

        The template file is expected in the directory templates/BACKEND_NAME.
        """
        template_dir = str(self.__class__.__name__).lower()
        template = self.jinja_env.get_template("/".join([template_dir, template_file]))
        self.update_config_file(target_file, template.render(template_vars))

    def _add_include_dir(self, f, incdirs, force_slash=False):
        if f.get("is_include_file"):
            _incdir = f.get("include_path") or os.path.dirname(f["name"]) or "."
            if force_slash:
                _incdir = _incdir.replace("\\", "/")
            if not _incdir in incdirs:
                incdirs.append(_incdir)
            return True
        return False

    def _param_value_str(self, param_value, str_quote_style="", bool_is_str=False):
        return jinja_filter_param_value_str(param_value, str_quote_style, bool_is_str)
