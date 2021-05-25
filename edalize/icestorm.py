# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

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
                    {'name' : 'nextpnr_options',
                     'type' : 'String',
                     'desc' : 'Additional options for nextpnr'},
                ]}
            Edatool._extend_options(options, Yosys)

            return {'description' : "Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and arachne-pnr or nextpnr for Place & Route",
                    'members' : options['members'],
                    'lists' : options['lists']}

    def configure_main(self):
        # Write yosys script file
        (src_files, incdirs) = self._get_fileset_files()
        yosys_synth_options = self.tool_options.get('yosys_synth_options', '')
        yosys_edam = {
                'files'         : self.files,
                'name'          : self.name,
                'toplevel'      : self.toplevel,
                'parameters'    : self.parameters,
                'tool_options'  : {'yosys' : {
                                        'arch' : 'ice40',
                                        'yosys_synth_options' : yosys_synth_options,
                                        'yosys_as_subtool' : True,
                                        'yosys_template' : self.tool_options.get('yosys_template'),
                                        }
                                }
                }

        yosys = getattr(import_module("edalize.yosys"), 'Yosys')(yosys_edam, self.work_root)
        yosys.configure()

        pcf_files = []
        for f in src_files:
            if f.file_type == 'PCF':
                pcf_files.append(f.name)
            elif f.file_type == 'user':
                pass

        if not pcf_files:
            pcf_files = ['empty.pcf']
            with open(os.path.join(self.work_root, pcf_files[0]), 'a'):
                os.utime(os.path.join(self.work_root, pcf_files[0]), None)
        elif len(pcf_files) > 1:
            raise RuntimeError("Icestorm backend supports only one PCF file. Found {}".format(', '.join(pcf_files)))

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
            depends = self.name+'.json'
            targets = self.name+'.asc'
            command = ['nextpnr-ice40', '-l', 'next.log']
            command += self.tool_options.get('nextpnr_options', [])
            command += ['--pcf' , pcf_files[0]]
            command += ['--json', depends]
            command += ['--asc' , targets]
            #CLI target
            commands.add(command, [targets], [depends])

            #GUI target
            commands.add(command+['--gui'], ["build-gui"], [depends])

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
