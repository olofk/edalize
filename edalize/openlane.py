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
                    'members': [
                        {'name' : 'interactive_name',
                         'type' : 'String',
                         'desc' : 'Optional name of interactive tcl script.'},
                    ],
                    'lists' : []}

    def configure_main(self):
        file_table = ""
        lefs = []
        blackbox_table = ""
        tcl_params = ""
        tcl_interactive = ""
        (src_files, incdirs) = self._get_fileset_files()
        for f in src_files:
            if f.file_type.startswith('verilogSource'):
                file_table = file_table + f.name + " "
            elif f.file_type.startswith('verilogBlackbox'):
                blackbox_table = blackbox_table + f.name + " "
            elif f.file_type == 'LEF':
                lefs.append(f.name)
            elif f.name.endswith('params.tcl'):
                tcl_params = f.name
            elif self.tool_options.get('interactive_name') != None:
                if f.name.endswith(self.tool_options.get('interactive_name')):
                    tcl_interactive = f.name

        template_vars = {
            'top' : self.toplevel,
            'file_table' : file_table,
            'blackbox_table' : blackbox_table,
            'lefs_table' : ' '.join(lefs),
            'work_root' : os.path.split(self.work_root)[1],
            'tcl_params' : tcl_params,
            'tcl_interactive' : tcl_interactive,
        }

        script_name = 'config.tcl'
        self.render_template('openlane-script-tcl.j2', script_name, template_vars)

        makefile_name = 'Makefile'
        self.render_template('openlane-makefile.j2', makefile_name, template_vars)
