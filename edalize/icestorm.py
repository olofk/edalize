# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.edatool import Edatool
from edalize.nextpnr import Nextpnr
from edalize.yosys import Yosys

class Icestorm(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                'members' : [
                    {'name' : 'pnr',
                     'type' : 'String',
                     'desc' : 'Select Place & Route tool. Legal values are *arachne* for Arachne-PNR, *next* for nextpnr or *none* to only perform synthesis. Default is next'},
                ],
                'lists' : [
                    {'name' : 'arachne_pnr_options',
                     'type' : 'String',
                     'desc' : 'Additional options for Arachnhe PNR'},
                ]}
            Edatool._extend_options(options, Yosys)
            Edatool._extend_options(options, Nextpnr)

            return {'description' : "Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and arachne-pnr or nextpnr for Place & Route",
                    'members' : options['members'],
                    'lists' : options['lists']}

    def configure_main(self):
        # Write yosys script file
        yosys_synth_options = self.tool_options.get('yosys_synth_options', '')

        #Pass icestorm tool options to yosys and nextpnr
        self.edam['tool_options'] = \
            {'yosys' : {
                'arch' : 'ice40',
                'yosys_synth_options' : yosys_synth_options,
                'yosys_as_subtool' : True,
                'yosys_template' : self.tool_options.get('yosys_template'),
            },
             'nextpnr' : {
                 'nextpnr_options' : self.tool_options.get('nextpnr_options', [])
             },
             }
        yosys = Yosys(self.edam, self.work_root)
        yosys.configure()

        pnr = self.tool_options.get('pnr', 'next')
        part = self.tool_options.get('part', None)
        if not pnr in ['arachne', 'next', 'none']:
            raise RuntimeError("Invalid pnr option '{}'. Valid values are 'arachne' for Arachne-pnr, 'next' for nextpnr or 'none' to only perform synthesis".format(pnr))

        # Write Makefile
        commands = self.EdaCommands()
        commands.commands = yosys.commands

        if pnr == 'arachne':
            depends = self.name+'.blif'
            targets = self.name+'.asc'
            command = ['arachne-pnr']
            command += self.tool_options.get('arachne_pnr_options', [])
            command += ['-p', depends, '-o', targets]
            commands.add(command, [depends], [targets])
            set_default_target(self.name+'.bin')
        elif pnr == 'next':
            nextpnr = Nextpnr(yosys.edam, self.work_root)
            nextpnr.flow_config = {'arch' : 'ice40'}
            nextpnr.configure()
            commands.commands += nextpnr.commands
            commands.set_default_target(self.name+'.bin')
        else:
            commands.set_default_target(self.name+'.json')

        #Image generation
        depends = self.name+'.asc'
        targets = self.name+'.bin'
        command = ['icepack', depends, targets]
        commands.add(command, [targets], [depends])

        #Timing analysis
        depends = self.name+'.asc'
        targets = self.name+'.tim'
        command = ['icetime', '-tmd', part or '', depends, targets]
        commands.add(command, [targets], [depends])
        commands.add([], ["timing"], [targets])

        #Statistics
        depends = self.name+'.asc'
        targets = self.name+'.stat'
        command = ['icebox_stat', depends, targets]
        commands.add(command, [targets], [depends])
        commands.add([], ["stats"], [targets])

        commands.write(os.path.join(self.work_root, 'Makefile'))
