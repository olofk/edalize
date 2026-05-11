# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import os
from typing import Any

from jinja2 import Environment, PackageLoader

from edalize.edam import Edam, File as EdamFile, RunArgs
from edalize.utils import EdaCommands

# Jinja2 tests and filters, available in all templates
def jinja_filter_param_value_str(
    value: Any,
    str_quote_style: str = "",
    bool_is_str: bool = False,
) -> str:
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
    TOOL_OPTIONS: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_tool_options(cls) -> dict[str, dict[str, Any]]:
        return cls.TOOL_OPTIONS

    # ``work_root`` is injected from outside (Edaflow.configure_tools) before
    # ``setup()`` is called, so declare it here for type-checkers.
    work_root: str

    def __init__(self) -> None:
        self.edam: Edam | None = None
        self.prev_nodes: set[Any] = set()
        self.jinja_env = Environment(
            loader=PackageLoader(__package__, "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self.jinja_env.filters["param_value_str"] = jinja_filter_param_value_str
        self.jinja_env.filters["generic_value_str"] = jinja_filter_param_value_str

    def _require_tool_option(self, option_name: str) -> Any:
        option = self.tool_options.get(option_name)
        if not option:
            raise RuntimeError(
                f"{self.__class__.__name__.lower()} requires tool option '{option_name}'"
            )
        return option

    def setup(self, edam: Edam) -> None:
        self.edam = edam
        try:
            self.name = edam["name"]
        except KeyError:
            raise RuntimeError("Missing required parameter 'name'")

        _tool_name = self.__class__.__name__.lower()

        self.tool_options: dict[str, Any] = (
            edam.get("tool_options", {}).get(_tool_name, {})
        )

        self.files = edam.get("files", [])
        # See note in legacy edatool.py.
        self.toplevel: Any = edam.get("toplevel", [])
        self.vpi_modules = edam.get("vpi", [])

        self.hooks = edam.get("hooks", {})
        self.parameters = edam.get("parameters", {})

        self.plusarg: dict[str, Any] = {}
        self.vlogparam: dict[str, Any] = {}
        self.vlogdefine: dict[str, Any] = {}
        self.generic: dict[str, Any] = {}
        self.cmdlinearg: dict[str, Any] = {}

        args: RunArgs = {}
        for k, v in self.parameters.items():
            args[k] = v.get("default")
        self._apply_parameters(args)

    def configure(self) -> None:
        self.write_config_files()

    # Subclasses implement this. Called at the end of configure
    def write_config_files(self) -> None:
        pass

    def update_config_file(self, file_name: str, contents: str) -> None:
        """
        Check contents against the file file_name in work_root.
        If these differ or file_name doesn't exist,
        write contents to file_name
        """
        f = os.path.join(self.work_root, file_name)
        if os.path.exists(f):
            old_file: str | None = open(f, "r").read()
        else:
            old_file = None
        if old_file != contents:
            with open(f, "w") as _f:
                _f.write(contents)

    def set_default_target(self, target: str) -> None:
        self.default_target = target

    def _apply_parameters(self, args: RunArgs) -> None:
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

    def render_template(
        self,
        template_file: str,
        target_file: str,
        template_vars: dict[str, Any] = {},
    ) -> None:
        """
        Render a Jinja2 template for the backend

        The template file is expected in the directory templates/BACKEND_NAME.
        """
        template_dir = str(self.__class__.__name__).lower()
        template = self.jinja_env.get_template("/".join([template_dir, template_file]))
        self.update_config_file(target_file, template.render(template_vars))

    def _add_include_dir(
        self,
        f: EdamFile,
        incdirs: list[str],
        force_slash: bool = False,
    ) -> bool:
        if f.get("is_include_file"):
            _incdir = f.get("include_path") or os.path.dirname(f["name"]) or "."
            if force_slash:
                _incdir = _incdir.replace("\\", "/")
            if not _incdir in incdirs:
                incdirs.append(_incdir)
            return True
        return False

    def _param_value_str(
        self,
        param_value: Any,
        str_quote_style: str = "",
        bool_is_str: bool = False,
    ) -> str:
        return jinja_filter_param_value_str(param_value, str_quote_style, bool_is_str)
