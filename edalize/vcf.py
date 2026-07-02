# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import re
import logging
import jinja2
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Vcf(Edatool):

    _description = """Synopsys Formal Backend

VC Formal is Synopsys's formal verification tool. 

example snippet of a a CAPI2 description file for VC Formal: 

.. code:: yaml

    vcf:
      app: [FPV]

"""
    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    tool_options = {
        "lists": {
            "app": "String",  # VC Formal App to Use
        }
    }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super(Vcf, self).__init__(edam, work_root, eda_api, verbose)

        # The list of RTL paths in the fileset (populated at configure time by
        # _get_file_names)
        self.rtl_paths = None

        # The list of include directories in the fileset (populated at configure time by
        # _get_file_names)
        self.incdirs = None

        # The name of the interpolated .tcl file that we create in the work
        # root
        self.tcl_name = "vcf.tcl"

    @staticmethod
    def get_doc(api_ver):
        if api_ver == 0:
            return {
                "description": "VCF formal verification tool",
                "lists": [
                    {"name": "app", "type": "String", "desc": ("VC Formal Application")}
                ],
            }

    def _get_file_names(self):
        """Read the fileset to get our file names"""
        assert self.rtl_paths is None

        src_files, self.incdirs = self._get_fileset_files()
        self.rtl_paths = []
        bn_to_path = {}
        tcl_names = []

        # RTL files have types verilogSource or systemVerilogSource*. We
        # presumably want some of them. The .tcl file has type vcfConfigTemplate: we
        # want exactly one of them.
        ft_re = re.compile(r"(:?systemV|v)erilogSource")
        for file_obj in src_files:
            if ft_re.match(file_obj.file_type):
                self.rtl_paths.append(file_obj.name)

                # Check that basenames are unique
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

            if file_obj.file_type == "vcfConfigTemplate":
                tcl_names.append(file_obj.name)
                continue

            # Ignore anything else

        if len(tcl_names) != 1:
            raise RuntimeError(
                "VCF expects exactly one file with type "
                "vcfConfigTemplate (the one called "
                "something.tcl.j2). We have {}.".format(tcl_names or "none")
            )

        return tcl_names[0]

    def _interpolate_tcl(self, src):
        """
        Interpolate the vcf targeted .tcl command file from its jinja2 template.

        Input file is a a jinja2 template that has the commands necessary to
        run VC Formal, sans the list of RTL files and include directories, as well
        as the desired application to use

        See class documentation for details of templating the .tcl file.
        """

        # This should be set by _get_file_names by now
        assert self.rtl_paths is not None

        src_path = os.path.join(self.work_root, src)
        dst_path = os.path.join(self.work_root, self.tcl_name)

        with open(src_path) as sf:
            try:
                template = self.jinja_env.from_string(sf.read())
            except jinja2.TemplateError as err:
                raise RuntimeError(
                    "Failed to load {!r} "
                    "as a Jijnja2 template: {}".format(src_path, err)
                )

        new_incdir = []
        for incdir in self.incdirs:
            new_incdir.append(f"+incdir+{incdir}")

        files = " ".join(new_incdir + self.rtl_paths)

        template_ctxt = {
            "app": self.tool_options.get("app"),
            "files": files,
            "top_level": self.toplevel,
        }

        with open(dst_path, "w") as df:
            df.write(template.render(template_ctxt))

    def configure_main(self):
        clean_tcl_name = self._get_file_names()
        self._interpolate_tcl(clean_tcl_name)

    def build_main(self, target=None):
        pass

    def run_main(self):
        self._run_tool(
            "vcf",
            [
                "-batch",
                f"-f {self.tcl_name}",
                "-output_log_file vcf.log",
                "-lic_wait 240",
            ],
        )
