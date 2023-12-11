# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import sys

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Efinity(Edatool):
    """
    Efinity Backend.

    The Efinity backend executes Efinity to build systems and program the FPGA
    """

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    TOOL_OPTIONS = {
        "family": {
            "type": "str",
            "desc": "FPGA family. Accepted is Trion and Titanium (default)",
        },
        "part": {
            "type": "str",
            "desc": "FPGA part number (e.g. Ti180M484)",
        },
        "timing": {
            "type": "str",
            "desc": "Speed grade (e.g. C4)",
        },
    }

    def setup(self, edam):
        """
        Create required files to make an Efinix build. Two files required:
        - XML project file
        - XML file with IO and hard blocks definitions (only done if an ISF file is included)
        """
        super().setup(edam)

        self.efinity_home = os.getenv("EFINITY_HOME")
        if self.efinity_home == None:
            raise RuntimeError("The environment variable EFINITY_HOME is not set.")

        if sys.platform == "win32" or sys.platform == "cygwin":
            self.efinity_python = self.efinity_home + "/python38/bin/python"
        else:
            self.efinity_python = self.efinity_home + "/bin/python3"

        for i in ["family", "part", "timing"]:
            if not i in self.tool_options:
                raise RuntimeError("Missing required option '{}'".format(i))

        design_files = []
        constr_files = []
        self.isf_file = None
        dep_files = []
        unused_files = []

        for f in self.files:
            _fn = f["name"]
            _ft = f.get("file_type", "")
            version = None
            if _ft.startswith("vhdlSource") or _ft.startswith("verilogSource"):
                version = ""
            elif _ft.startswith("systemVerilogSource"):
                version = "sv_09"

            if version is not None:
                f["version"] = version
                design_files.append(f)
                dep_files.append(_fn)
            elif _ft == "SDC":
                constr_files.append(_fn)
                dep_files.append(_fn)
            elif _ft == "ISF":
                if self.isf_file:
                    raise RuntimeError(
                        "The Efinity backend only supports a single ISF file."
                    )
                self.isf_file = _fn
            else:
                unused_files.append(f)

        bit_file = os.path.join("outflow", self.name + ".bit")
        self.edam = edam.copy()

        self.edam["files"] = unused_files
        self.edam["files"].append(
            {
                "name": bit_file,
            }
        )

        self.template_vars = {
            "name": self.name,
            "design_files": design_files,
            "constr_files": constr_files,
            "tool_options": self.tool_options,
            "toplevel": self.toplevel,
            "vlogparam": self.vlogparam,
            "vlogdefine": self.vlogdefine,
            "generic": self.generic,
        }

        commands = EdaCommands()

        if self.isf_file:
            # Run script to generate .peri.xml from isf
            commands.add(
                [
                    self.efinity_python,
                    "isf_to_xml.py",
                    self.name,
                    self.tool_options.get("part"),
                    self.isf_file,
                ],
                [self.name + ".peri.xml"],
                [self.isf_file],
                variables={"EFXPT_HOME": self.efinity_home + "/pt"},
            )
            dep_files.append(self.name + ".peri.xml")

        commands.add(
            [
                self.efinity_python,
                os.path.join(self.efinity_home, "scripts", "efx_run.py"),
                "--prj",
                self.name + ".xml",
                "--flow",
                "compile",
            ],
            [bit_file],
            dep_files,
            variables={
                "EFXPT_HOME": self.efinity_home + "/pt",
                "EFXPGM_HOME": self.efinity_home + "/pgm",
            },
        )
        commands.set_default_target(bit_file)
        self.commands = commands

    def write_config_files(self):
        # Render XML project file
        self.render_template(
            "newproj_tmpl.xml.j2", self.name + ".xml", self.template_vars
        )

        if self.isf_file:
            # Create XML file with IO and hard blocks definitions
            self.render_template("isf_to_xml.py", "isf_to_xml.py")
