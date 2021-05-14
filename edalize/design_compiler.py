# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

logger = logging.getLogger(__name__)

""" design-compiler Backend

A core (usually the system core) can add the following files:

- Standard design sources

- Constraints: Supply xdc files with file_type=xdc or unmanaged constraints with file_type SDC

- IP: Supply the IP core xci file with file_type=xci and other files (like .prj)
      as file_type=user
"""
class Design_compiler(Edatool):

    argtypes = ['vlogdefine', 'vlogparam', 'generic']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "The Vivado backend executes Xilinx Vivado to build systems and program the FPGA",
                    'members' : [
                        {'name' : 'vivado-settings',
                         'type' : 'String',
                         'desc' : 'Path to vivado settings (e.g. /opt/Xilinx/Vivado/2017.2/settings64.sh)'},
                        {'name' : 'part',
                         'type' : 'String',
                         'desc' : 'FPGA part number (e.g. xc7a35tcsg324-1)'},
                        {'name' : 'synth',
                         'type' : 'String',
                         'desc' : 'Synthesis tool. Allowed values are vivado (default) and yosys.'},
                        {'name' : 'pnr',
                         'type' : 'String',
                         'desc' : 'P&R tool. Allowed values are vivado (default) and none (to just run synthesis)'},
                        {'name' : 'jobs',
                         'type' : 'Integer',
                         'desc' : 'Number of jobs. Useful for parallelizing OOC (Out Of Context) syntheses.'},
                        {'name' : 'jtag_freq',
                        'type' : 'Integer',
                        'desc' : 'The frequency for jtag communication'},
                        {'name' : 'source_mgmt_mode',
                        'type' : 'String',
                        'desc' : 'Source managment mode. Allowed values are None (unmanaged, default), DisplayOnly (automatically update sources) and All (automatically update sources and compile order)'},
                        {'name' : 'hw_target',
                        'type' : 'Description',
                        'desc' : 'Board identifier (e.g. */xilinx_tcf/Digilent/123456789123A'},
                    ]}

    """ Get tool version

    This gets the Vivado version by running vivado -version and
    parsing the output. If this command fails, "unknown" is returned
    """
    def get_version(self):

        version = "unknown"
        try:
            vivado_text = subprocess.Popen(["vivado", "-version"], stdout=subprocess.PIPE, env=os.environ).communicate()[0]
            version_exp = r'Vivado.*(?P<version>v.*) \(.*'

            match = re.search(version_exp, str(vivado_text))
            if match is not None:
                version = match.group('version')
        except Exception:
            logger.warning("Unable to recognize Vivado version")

        return version

    """ Configuration is the first phase of the build
    This writes the project TCL files and Makefile. It first collects all
    sources, IPs and constraints and then writes them to the TCL file along
     with the build steps.
    """
    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self.jinja_env.filters["src_file_filter"] = self.src_file_filter

        has_vhdl = "vhdlSource" in [x.file_type for x in src_files]
        has_vhdl2008 = "vhdlSource-2008" in [x.file_type for x in src_files]
        has_xci = "xci" in [x.file_type for x in src_files]

        self.synth_tool = self.tool_options.get("synth", "design-compiler")


        template_vars = {
            'name'         : self.name,
            'src_files'    : src_files,
            'incdirs'      : incdirs+['.'],
            'tool_options' : self.tool_options,
            'toplevel'     : self.toplevel,
            'vlogparam'    : self.vlogparam,
            'vlogdefine'   : self.vlogdefine,
            'generic'      : self.generic,
            'has_vhdl2008' : has_vhdl2008,
            'has_xci'      : has_xci,
        }

        design_compiler_settings = self.tool_options.get('design_compiler-settings', None)
        design_compiler_command = "source {} && design_compiler".format(design_compiler_settings) if design_compiler_settings else "design_compiler"
        
        self.render_template('design-compiler-makefile.j2',
                             'Makefile',
                             {'name' : self.name,
                              'part' : self.tool_options.get('part', ""),
                              'bitstream' : self.name+'.bit',
                              'yosys' : True if self.synth_tool == 'yosys' else None,
                              'design_compiler_command_command': design_compiler_command
                              })
                              
                              
        jobs = self.tool_options.get('jobs', None)

        run_template_vars = {
            'jobs' : ' -jobs ' + str(jobs) if jobs is not None else ''
        }
        self.render_template('design-compiler-run.tcl.j2',
                             self.name+"_run.tcl",
                             run_template_vars)
                             
        self.render_template('design-compiler-read-sources.tcl.j2',
                             self.name + '-read-sources.tcl',
                             template_vars)

        

        

        # synth_template_vars = {
            # 'jobs' : ' -jobs ' + str(jobs) if jobs is not None else ''
        # }

        # self.render_template('vivado-synth.tcl.j2',
                             # self.name+"_synth.tcl",
                             # synth_template_vars)



        

        # self.render_template('vivado-program.tcl.j2',
                             # self.name+"_pgm.tcl")

    def src_file_filter(self, f):
        def _vhdl_source(f):
            s = 'read_vhdl'
            if f.file_type == 'vhdlSource-2008':
                s += ' -vhdl2008'
            if f.logical_name:
                s += ' -library '+f.logical_name
            return s

        file_types = {
            'verilogSource'       : 'analyze -format verilog -work work',
            'systemVerilogSource' : 'analyze -format sverilog -work work',
            'vhdlSource'          : _vhdl_source(f),
            'xci'                 : 'read_ip',
            'xdc'                 : 'read_xdc',
            'tclSource'           : 'source',
            'SDC'                 : 'read_xdc -unmanaged',
            'mem'                 : 'read_mem',
        }
        _file_type = f.file_type.split('-')[0]
        if _file_type in file_types:
            return file_types[_file_type] + ' ' + f.name

        if _file_type == 'user':
            return ''

        _s = "{} has unknown file type '{}', interpretation is up to Vivado"
        logger.warning(_s.format(f.name,
                                    f.file_type))
        return 'add_files -norecurse' + ' ' + f.name

    def build_main(self):
        logger.info("Building")
        args = []
        if 'pnr' in self.tool_options:
            if self.tool_options['pnr'] == 'vivado':
                pass
            elif self.tool_options['pnr'] == 'none':
                args.append('synth')
        #self._run_tool('make', args, quiet=True)
        self._run_tool('make', args, quiet=False)

    """ Program the FPGA

    For programming the FPGA a vivado tcl script is written that searches for the
    correct FPGA board and then downloads the bitstream. The tcl script is then
    executed in Vivado's batch mode.
    """
    def run_main(self):
        if 'pnr' in self.tool_options:
            if self.tool_options['pnr'] == 'vivado':
                pass
            elif self.tool_options['pnr'] == 'none':
                return

        self._run_tool('make', ['pgm'])
