# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
from pathlib import Path
import re
import shutil

from edalize.edatool import Edatool


class Openroad(Edatool):

    _description = """OpenROAD-flow-scripts
    """

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "Open source flow for ASIC synthesis, placement and routing",
                "members": [
                    {
                        "name": "flow_path",
                        "type": "String",
                        "desc": "Path to OpenROAD-flow-script/flow",
                    },
                    {
                        "name": "make_target",
                        "type": "String",
                        "desc": "make target (default: finish)",
                    },
                ],
                "lists": [],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super(Openroad, self).__init__(edam, work_root, eda_api, verbose)

        # The list of RTL paths in the fileset (populated at configure time by
        # _get_file_names)
        self.rtl_paths = None

        # The list of include directories in the fileset (populated at
        # configure time by _get_file_names)
        self.incdirs = None

    def _get_file_names(self):
        """Read the fileset to get our file names"""
        assert self.rtl_paths is None

        src_files, self.incdirs = self._get_fileset_files()
        self.rtl_paths = []
        bn_to_path = {}

        # RTL files have types verilogSource or systemVerilogSource*
        ft_re = re.compile(r"(:?systemV|v)erilogSource")
        for file_obj in src_files:
            if ft_re.match(file_obj.file_type):
                self.rtl_paths.append(file_obj.name)
                basename = os.path.basename(file_obj.name)
                if basename in bn_to_path:
                    raise RuntimeError(
                        "More than one RTL file with the same"
                        "basename: {!r} and {!r}.".format(
                            bn_to_path[basename], file_obj.name
                        )
                    )

                bn_to_path[basename] = file_obj.name
                continue

    def _dump_file_lists(self):
        """
        Dump the list of RTL files and incdirs in work_root.

        This is useful if you need to run some sort of hook that consumes the
        list of files (to run sv2v in place on them, for example). The list of
        RTL files goes to files.txt and the list of include directories goes to
        incdirs.txt.
        """
        with open(os.path.join(self.work_root, "files.txt"), "w") as handle:
            handle.write("\n".join(self.rtl_paths) + "\n")
        with open(os.path.join(self.work_root, "incdirs.txt"), "w") as handle:
            handle.write("\n".join(self.incdirs) + "\n")

    def configure_main(self):
        self._get_file_names()
        self._dump_file_lists()

        if "flow_path" not in self.tool_options:
            raise RuntimeError(
                "'" + self.name + "' miss a mandatory parameter 'flow_path'"
            )

        if not self.toplevel:
            raise RuntimeError(
                "'" + self.name + "' miss a mandatory parameter 'toplevel'"
            )

        if "make_target" not in self.tool_options:
            self.make_target = "finish"
        else:
            self.make_target = self.tool_options["make_target"]

        flow_path = Path(self.tool_options["flow_path"])
        base_path = Path(self.work_root).parent.parent.parent
        self.flow_path = os.path.join(base_path, flow_path)

        print("path", self.flow_path)
        src_files, self.incdirs = self._get_fileset_files()

        self.config_file = None
        self.constraint_file = None
        self.make_file = None

        for file in src_files:
            if file.file_type.startswith("Makefile"):
                if self.make_file is not None:
                    raise RuntimeError(
                        f"{self.name} multiple make files passed {self.make_file.logical_name} and {file.logical_name}"
                    )
                self.make_file = file
            if file.file_type.startswith("configFile"):
                if self.config_file is not None:
                    raise RuntimeError(
                        f"{self.name} multiple config files passed {self.config_file.logical_name} and {file.logical_name}"
                    )
                self.config_file = file
            if file.file_type.startswith("SDC"):
                if self.constraint_file is not None:
                    raise RuntimeError(
                        f"{self.name} multiple constraint (SDC) files passed {self.constraint_file.logical_name} and {file.logical_name}"
                    )
                self.constraint_file = file

        if any(
            f is None for f in [self.config_file, self.constraint_file, self.make_file]
        ):
            raise RuntimeError(
                f"{self.name} one or more files need to be passed: \n"
                f"constraint_file: {self.constraint_file.name if self.constraint_file else 'NEEDED'} \n"
                f"config_file: {self.config_file.name if self.config_file else 'NEEDED'} \n"
                f"make_file: {self.make_file.name if self.make_file else 'NEEDED'} \n"
            )
        else:
            for f in [self.config_file, self.constraint_file, self.make_file]:
                print(
                    "file",
                    self.work_root,
                    f.name,
                    os.path.join(self.work_root, f.name),
                )
            shutil.copyfile(
                os.path.join(self.work_root, self.config_file.name),
                os.path.join(self.work_root, "config.mk"),
            )
            shutil.copyfile(
                os.path.join(self.work_root, self.constraint_file.name),
                os.path.join(self.work_root, "constraint.sdc"),
            )
            shutil.copyfile(
                os.path.join(self.work_root, self.make_file.name),
                os.path.join(self.work_root, "Makefile"),
            )

    def build_main(self):
        pass

    def run_main(self):
        print("run_main")
        args = [
            "DESIGN_CONFIG=./config.mk",
            f"FLOW_HOME={self.flow_path}",
            f"DESIGN_NAME={self.toplevel}",
            "SHELL=/bin/bash",
            self.make_target,
        ]

        self._run_tool("make", args)
