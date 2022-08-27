# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import glob
import os
from pathlib import Path
import re
import shutil
import subprocess

from edalize.edatool import Edatool


class Export(Edatool):

    _description = """Cocotb
    """

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "Export design",
                "members": [],
                "lists": [],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super(Export, self).__init__(edam, work_root, eda_api, verbose)

        # The list of RTL paths in the fileset (populated at configure time by
        # _get_file_names)
        self.rtl_paths = None

        # The list of include directories in the fileset (populated at
        # configure time by _get_file_names)
        self.incdirs = None
        self.src_files = None

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

        self.src_files, self.incdirs = self._get_fileset_files()

    def build_main(self):
        pass

    def run_main(self):
        # cat files.txt | xargs cat > design.v
        files_path = [os.path.join(self.work_root, file) for file in self.rtl_paths]
        with open('design.v', 'w') as outfile:
            for fname in files_path:
                with open(fname) as infile:
                    for line in infile:
                        outfile.write(line)
