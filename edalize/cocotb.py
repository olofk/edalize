# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import glob
import os
from pathlib import Path
import re
import shutil

from edalize.edatool import Edatool


class Cocotb(Edatool):

    _description = """Cocotb
    """

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "Cocotb tool for testbenches in python",
                "members": [
                    {
                        "name": "make_args",
                        "type": "String",
                        "desc": "make args: example: (SIM=verilator)",
                    },
                ],
                "lists": [],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super(Cocotb, self).__init__(edam, work_root, eda_api, verbose)

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

        src_files, self.incdirs = self._get_fileset_files()

        self.make_file = None
        self.cocotb_test_file = None

        for file in src_files:
            if file.file_type.startswith("Makefile"):
                if self.make_file is not None:
                    raise RuntimeError(
                        f"{self.name} multiple make files passed {self.make_file.logical_name} and {file.logical_name}"
                    )
                self.make_file = file
            if file.file_type.startswith("Cocotb"):
                if self.cocotb_test_file is not None:
                    raise RuntimeError(
                        f"{self.name} cocotb python files passed {self.make_file.logical_name} and {file.logical_name}"
                    )
                self.cocotb_test_file = file

        if any(
            f is None for f in [self.make_file, self.cocotb_test_file]
        ):
            raise RuntimeError(
                f"{self.name} one or more files need to be passed: \n"
                f"make_file: {self.make_file.name if self.make_file else 'NEEDED'} \n"
                f"cocotb_python_file: {self.cocotb_test_file.name if self.cocotb_test_file else 'NEEDED'} \n"
            )
        else:
            for f in [self.make_file, self.cocotb_test_file]:
                print(
                    "file",
                    self.work_root,
                    f.name,
                    os.path.join(self.work_root, f.name),
                )
            shutil.copyfile(
                os.path.join(self.work_root, self.make_file.name),
                os.path.join(self.work_root, "Makefile"),
            )
            shutil.copyfile(
                os.path.join(self.work_root, self.cocotb_test_file.name),
                os.path.join(self.work_root, os.path.basename(self.cocotb_test_file.name)),
            )

    def build_main(self):
        pass

    def run_main(self):
        args = [
            "SHELL=/bin/bash",
        ]
        if "make_args" in self.tool_options:
            for arg in self.tool_options["make_args"].split(" "):
                if len(arg):
                    args.append(arg)

        return_code, _, _ = self._run_tool("make", args)

        at_least_one_test_failed = 0
        with open(f"{self.work_root}/results.xml") as f:
            if "<failure />" in f.read():
                at_least_one_test_failed = 1

        if return_code + at_least_one_test_failed > 0:
            print("Cocotb test FAILED")
        exit(return_code + at_least_one_test_failed)
