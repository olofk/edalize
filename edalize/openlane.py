# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Openlane(Edatool):

    argtypes = ["vlogdefine"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "Open source flow for ASIC synthesis, placement and routing",
                "members": [],
                "lists": [],
            }

    def configure_main(self):
        files = []
        tcl = []

        (src_files, incdirs) = self._get_fileset_files()
        for f in src_files:
            if f.file_type.startswith("verilogSource"):
                files.append(f.name)
            elif f.file_type.startswith("systemVerilogSource"):
                files.append(f.name)
            elif f.file_type == "tclSource":
                tcl.append(f.name)

        defines = ""
        for k, v in self.vlogdefine.items():
            defines += " {}={}".format(k, self._param_value_str(v))

        template_vars = {
            "top": self.toplevel,
            "file_table": " ".join(files),
            "tcl": "\n".join(["source " + f for f in tcl]),
            "defines": defines,
        }

        script_name = "config.tcl"
        self.render_template("openlane-script-tcl.j2", script_name, template_vars)

        makefile_name = "Makefile"
        self.render_template("openlane-makefile.j2", makefile_name, template_vars)
