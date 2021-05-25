# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.edatool import Edatool

class Nextpnr(Edatool):

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "a portable FPGA place and route tool",
                    'members' : [],
                    'lists' : [
                        {'name' : 'nextpnr_options',
                         'type' : 'String',
                         'desc' : 'Additional options for nextpnr'},
                        ]}

    def configure_main(self):
        pcf_file = ""
        netlist = ""
        unused_files = []
        for f in self.files:
            if f['file_type'] == 'PCF':
                if pcf_file:
                    raise RuntimeError("Nextpnr only support one PCF file. Found {} and {}".format(pcf_file, f['name']))
                pcf_file = f['name']
            elif f['file_type'] == 'jsonNetlist':
                if netlist:
                    raise RuntimeError("Nextpnr only support one netlist. Found {} and {}".format(netlist, f['name']))
                netlist = f['name']
            else:
                unused_files.append(f)

        self.edam['files'] = unused_files
        of = [
            {'name' : self.name+'.asc', 'file_type' : 'iceboxAscii'},
        ]
        self.edam['files'] += of

        # Write Makefile
        commands = self.EdaCommands()

        depends = netlist
        targets = self.name+'.asc'
        command = ['nextpnr-'+self.flow_config['arch'], '-l', 'next.log']
        command += self.tool_options.get('nextpnr_options', [])
        command += ['--pcf' , pcf_file] if pcf_file else []
        command += ['--json', depends]
        command += ['--asc' , targets]

        #CLI target
        commands.add(command, [targets], [depends])

        #GUI target
        commands.add(command+['--gui'], ["build-gui"], [depends])
        self.commands = commands.commands
