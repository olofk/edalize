# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

logger = logging.getLogger(__name__)


class Ghdl(Edatool):

    description = "GHDL is an open source VHDL simulator, which fully supports IEEE 1076-1987, IEEE 1076-1993, IEE 1076-2002 and partially the 1076-2008 version of VHDL"

    TOOL_OPTIONS = {
        "mode": {
            "type": "str",
            "desc": "Select operation mode. verilog to create verilog, sim to run simulation. Default sim",
        }
    }  # Analyze options, elab options, run_options

    def setup(self, edam):
        super().setup(edam)
        analyze_options = self.tool_options.get("analyze_options", [])

        # Check of std=xx analyze option, this overyides the dynamic determination of vhdl standard
        import re

        rx = re.compile("^--std=([0-9]+)")
        m = None
        for o in analyze_options:
            m = rx.match(o)
            if m:
                stdarg = [m.group()]
                analyze_options.remove(o)
                break

        if m:
            logger.warning(
                "Analyze option "
                + m.group()
                + " given, will override any vhdlSource-xxxx specification\n"
            )
            standard = m.group(1)
        else:
            # ghdl does not support mixing incompatible versions
            # specifying 93c as std should allow 87 syntax
            # 2008 can't be combined so try to parse everthing with 08 std

            has87 = has93 = has08 = False
            for f in self.files:
                file_type = f.get("file_type", "")
                if file_type == "vhdlSource-87":
                    has87 = True
                elif file_type == "vhdlSource-93":
                    has93 = True
                elif file_type == "vhdlSource-2008":
                    has08 = True
            stdarg = []
            if has08:
                if has87 or has93:
                    logger.warning(
                        "ghdl can't mix vhdlSource-2008 with other standard version\n"
                        + "Trying with treating all as vhdlSource-2008"
                    )
                stdarg = ["--std=08"]
            elif has87 and has93:
                stdarg = ["--std=93c"]
            elif has87:
                stdarg = ["--std=87"]
            elif has93:
                stdarg = ["--std=93"]
            else:
                stdarg = ["--std=93c"]

            standard = rx.match(stdarg[0]).group(1)

        run_options = self.tool_options.get("run_options", [])

        analyze_options = " ".join(analyze_options)

        _vhdltypes = ("vhdlSource", "vhdlSource-87", "vhdlSource-93", "vhdlSource-2008")

        libraries = {}
        library_options = "--work={lib} --workdir=./{lib}"
        ghdlimport = ""
        vhdl_sources = ""

        # GHDL versions older than 849a25e0 don't support the dot notation (e.g.
        # my_lib.top_design) for the top level.
        # Nonetheless, we unconditionally split the library and the primary unit,
        # if the user specified the top level using the dot notation.
        top = self.toplevel.split(".")

        if len(top) > 2:
            logger.error("Invalid dot notation in toplevel: {}".format(self.toplevel))

        top_libraries = ""

        if len(top) > 1:
            libraries[top[0]] = []
            top_libraries = library_options.format(lib=top[0])

        top_unit = top[-1]

        unused_files = []
        for f in self.files:
            if f.get("file_type") in _vhdltypes:
                # Files without a specified library will by added to
                # libraries[None] which is perhaps poor form but avoids
                # conflicts with user generated names
                libraries[f["logical_name"]] = libraries.get(f["logical_name"], []) + [
                    f["name"]
                ]
                vhdl_sources += " {file}".format(file=f["name"])
                depfiles.append(f)
            else:
                unused_files.append(f)

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        ghdlimport = ""
        make_libraries_directories = ""

        for lib, files in libraries.items():
            lib_opts = ""
            if lib:
                analyze_options += " -P./{}".format(lib)
                make_libraries_directories += "\tmkdir -p {}\n".format(lib)
                lib_opts = library_options.format(lib=lib)
            ghdlimport += "\tghdl -i $(STD) $(ANALYZE_OPTIONS) {} {}\n".format(
                lib_opts, " ".join(files)
            )

        commands = EdaCommands()
        if self.tool_options.get("mode") == "verilog":
            commands.add(
                ["ghdl", "-a"] + stdarg + analyze_options + [top_libraries, top_unit],
                # FIXME: Get names of object files here
                [f"work-obj{stdarg[0]}.cf"],
                depfiles,
            )
            commands.set_default_target(f"work-obj{stdarg[0]}.cf")
        self.commands = commands

    def run_main(self):
        cmd = "make"
        args = ["run"]

        # GHDL doesn't support Verilog, but the backend used vlogparam since
        # edalize didn't support generic at the time. Now that generic support
        # has been added support for vlogparam is deprecated and will be
        # removed in the future. For now support either option.

        if self.vlogparam:
            logger.warning(
                "GHDL backend support for vlogparam is deprecated and will be removed.\n"
                + "Use generic instead."
            )

        if self.vlogparam or self.generic:
            extra_options = "EXTRA_OPTIONS="
            for d in [self.vlogparam, self.generic]:
                for k, v in d.items():
                    extra_options += " -g{}={}".format(
                        k, self._param_value_str(v, '"', bool_is_str=True)
                    )
            args.append(extra_options)
        self._run_tool(cmd, args)
