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
                        {'name' : 'clk_name',
                        'type' : 'String',
                        'desc' : 'Name of the clock signal in the design.'},
                        {'name' : 'clk_period',
                        'type' : 'String',
                        'desc' : 'Period in nanoseconds of the design clock'},
                    ],
                    'lists' : []}

    # At a minimum, we need our source Verilog files and locations to run Openlane
    # For a minimal example, we can leave everything else as default (to be changed later)
    def configure_main(self):
        file_table = ""
        (src_files, incdirs) = self._get_fileset_files()
        for f in src_files:
            file_table = file_table + f.name + " "

        clk_name = self.tool_options.get('clk_name')
        if clk_name == None:
            logger.error("Openlane backend must have the tool option clk_name set.")
            return

        clk_period = self.tool_options.get('clk_period')
        if clk_period == None:
            logger.error("Openlane backend must have the tool option clk_period set (in nanoseconds).")
            return

        template_vars = {
            'top' : self.toplevel,
            'file_table' : file_table,
            'work_root' : os.path.split(self.work_root)[1],
            'clk_name' : clk_name,
            'clk_period' : clk_period,
        }

        script_name = 'config.tcl'
        self.render_template('openlane-script-tcl.j2', script_name, template_vars)

        makefile_name = 'Makefile'
        self.render_template('openlane-makefile.j2', makefile_name, template_vars)