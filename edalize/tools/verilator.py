# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands
from edalize.verilator import Verilator as EdalizeVerilator


class Verilator(Edatool):
    description = "Verilator, the fastest Verilog/SystemVerilog simulator"

    TOOL_OPTIONS = {
        "exe": {
            "type": "str",
            "desc": "Controls whether to create an executable. Set to 'false' when something else will do the final linking",
        },
        "make_options": {
            "type": "str",
            "desc": "Additional arguments passed to make when compiling the simulation. This is commonly used to set OPT/OPT_FAST/OPT_SLOW.",
        },
        "mode": {
            "type": "str",
            "desc": "Select compilation mode. Use *none* for no compilation mode. Legal values are *binary*, *cc*, *dpi-hdr-only*, *lint-only*, *none*, *preprocess-only*, *sc*, *xml-only*. See Verilator documentation for function: https://veripool.org/guide/latest/exe_verilator.html",
        },
        "gen-xml": {
            "type": "bool",
            "desc": "Generate XML output",
        },
        "gen-dpi-hdr": {
            "type": "bool",
            "desc": "Generate DPI header output",
        },
        "gen-preprocess": {
            "type": "bool",
            "desc": "Generate preprocessor output",
        },
        "verilator_options": {
            "type": "str",
            "desc": "Additional options for verilator",
            "list": True,
        },
        # run_options?
    }

    def setup(self, edam):
        super().setup(edam)

        # Future improvement: Separate include directories of c and verilog files
        incdirs = []

        verilator_file = self.name + ".vc"

        vc = []
        vc.append("--Mdir .")

        # Default to cc mode if not specified
        mode = self.tool_options.get("mode", "cc")

        if mode not in EdalizeVerilator.modes:
            _s = "Illegal verilator mode {}. Allowed values are {}"
            raise RuntimeError(_s.format(mode, ", ".join(EdalizeVerilator.modes)))
        vc.append("--" + mode)

        vc += self.tool_options.get("verilator_options", [])

        vlt_files = []
        vlog_files = []
        opt_c_files = []
        uhdm_files = []

        unused_files = []
        depfiles = [verilator_file]
        for f in self.files:
            file_type = f.get("file_type", "")
            depfile = True
            if file_type.startswith("systemVerilogSource") or file_type.startswith(
                "verilogSource"
            ):
                if not self._add_include_dir(f, incdirs):
                    vlog_files.append(f["name"])
            elif file_type in ["cppSource", "systemCSource", "cSource"]:
                depfile = False
                if not self._add_include_dir(f, incdirs):
                    opt_c_files.append(f["name"])
            elif file_type == "vlt":
                vlt_files.append(f["name"])
            elif file_type == "uhdm":
                uhdm_files.append(f["name"])
            else:
                unused_files.append(f)
                depfile = False

            if depfile:
                depfiles.append(f["name"])

        # Add created exe/.so/.a to EDAM output files?
        self.edam = edam.copy()
        self.edam["files"] = unused_files

        if uhdm_files:
            vc.append("--uhdm-ast-sv")

        for include_dir in incdirs:
            vc.append(f"+incdir+" + include_dir)
            vc.append("-CFLAGS -I" + include_dir)

        vc += vlt_files + uhdm_files + vlog_files

        vc.append(f"--top-module {self.toplevel}\n")
        if str(self.tool_options.get("exe")).lower() != "false":
            vc.append("--exe")

        vc += opt_c_files

        for k, v in self.vlogparam.items():
            vc.append(
                "-G{}={}".format(k, self._param_value_str(v, str_quote_style='\\"'))
            )
        for k, v in self.vlogdefine.items():
            vc.append("-D{}={}".format(k, self._param_value_str(v)))

        self.vc = vc

        mk_file = f"V{self.toplevel}.mk"
        exe_file = f"V{self.toplevel}"
        commands = EdaCommands()
        commands.add(
            ["verilator", "-f", verilator_file],
            [mk_file],
            depfiles,
        )

        if mode in [
            "binary",
            "dpi-hdr-only",
            "lint-only",
            "preprocess-only",
            "xml-only",
        ]:
            commands.set_default_target(mk_file)
        else:
            commands.add(
                ["make", "-f", mk_file] + self.tool_options.get("make_options", []),
                [exe_file],
                [mk_file] + opt_c_files,
            )
            commands.set_default_target(exe_file)

        self.commands = commands

    def write_config_files(self):
        self.update_config_file(self.name + ".vc", "\n".join(self.vc) + "\n")

    def run(self):
        self.args = []
        for key, value in self.plusarg.items():
            self.args += ["+{}={}".format(key, self._param_value_str(value))]
        for key, value in self.cmdlinearg.items():
            self.args += ["--{}={}".format(key, self._param_value_str(value))]

        self.args += self.tool_options.get("run_options", [])

        # Default to cc mode if not specified
        if "mode" not in self.tool_options:
            self.tool_options["mode"] = "cc"
        if self.tool_options["mode"] in [
            "dpi-hdr-only",
            "lint-only",
            "preprocess-only",
            "xml-only",
        ]:
            return
        return ("./V" + self.toplevel, self.args, self.work_root)
