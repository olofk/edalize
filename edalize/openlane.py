# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Openlane(Edatool):

    argtypes = []

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Open source flow for ASIC synthesis, placement and routing",
                    'members': [],
                    'lists' : []}

    def configure_main(self):
        file_table = ""
        tcl_params = ""
        (src_files, incdirs) = self._get_fileset_files()
        for f in src_files:
            if f.file_type.startswith('verilogSource'):
                file_table = file_table + f.name + " "
            elif f.file_type.startswith('tclSource'):
                tcl_params = f.name

        template_vars = {
            'top' : self.toplevel,
            'file_table' : file_table,
            'work_root' : os.path.split(self.work_root)[1],
            'tcl_params' : tcl_params,
        }

        script_name = 'config.tcl'
        self.render_template('openlane-script-tcl.j2', script_name, template_vars)

        makefile_name = 'Makefile'
        self.render_template('openlane-makefile.j2', makefile_name, template_vars)