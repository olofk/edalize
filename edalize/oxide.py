# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.edatool import Edatool
from edalize.nextpnr import Nextpnr
from edalize.yosys import Yosys

class Oxide(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                'lists' : [],
                'members' : [
                    {'name' : 'device',
                     'type' : 'String',
                     'desc' : 'Required device option for nextpnr-nexus command (e.g. LIFCL-40-9BG400C)'},
                ]}

            Edatool._extend_options(options, Yosys)
            Edatool._extend_options(options, Nextpnr)

            return {'description' : "Project Oxide enables a fully open-source flow for Nexus FPGAs using Yosys for Verilog synthesis and nextpnr for place and route",
                    'members' : options['members'],
                    'lists'   : options['lists']}

    def configure_main(self):
        #Pass trellis tool options to yosys and nextpnr
        self.edam['tool_options'] = \
            {'yosys' : {
                'arch' : 'nexus',
                'yosys_synth_options' : self.tool_options.get('yosys_synth_options', []),
                'yosys_as_subtool' : True,
                'yosys_template' : self.tool_options.get('yosys_template'),
            },
             'nextpnr' : {
                 'device'          : self.tool_options.get('device'),
                 'nextpnr_options' : self.tool_options.get('nextpnr_options', [])
             },
             }

        yosys = Yosys(self.edam, self.work_root)
        yosys.configure()

        nextpnr = Nextpnr(yosys.edam, self.work_root)
        nextpnr.flow_config = {'arch' : 'nexus'}
        nextpnr.configure()

        # Write Makefile
        commands = self.EdaCommands()
        commands.commands = yosys.commands

        commands.commands += nextpnr.commands

        #Image generation
        depends = self.name+'.fasm'
        targets = self.name+'.bit'
        command = ['prjoxide', 'pack', depends, targets]
        commands.add(command, [targets], [depends])

        commands.set_default_target(self.name+'.bit')
        commands.write(os.path.join(self.work_root, 'Makefile'))
