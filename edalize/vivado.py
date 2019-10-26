import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

""" Vivado Backend

A core (usually the system core) can add the following files:

- Standard design sources

- Constraints: Supply xdc files with file_type=xdc or unmanaged constraints with file_type SDC

- IP: Supply the IP core xci file with file_type=xci and other files (like .prj)
      as file_type=user
"""
class Vivado(Edatool):

    argtypes = ['vlogdefine', 'vlogparam', 'generic']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "The Vivado backend executes Xilinx Vivado to build systems and program the FPGA",
                    'members' : [
                        {'name' : 'part',
                         'type' : 'String',
                         'desc' : 'FPGA part number (e.g. xc7a35tcsg324-1)'},
                        {'name' : 'pnr',
                         'type' : 'String',
                         'desc' : 'P&R tool. Allowed values are vivado (default) and none (to just run synthesis)'},
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
        except Exception as ex:
            logger.warning("Unable to recognize Vivado version")

        return version

    """ Configuration is the first phase of the build
    This writes the project TCL files and Makefile. It first collects all
    sources, IPs and constraints and then writes them to the TCL file along
     with the build steps.
    """
    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self.jinja_env.filters['src_file_filter'] = self.src_file_filter

        has_vhdl2008 = 'vhdlSource-2008' in [x.file_type for x in src_files]
        has_xci      = 'xci'             in [x.file_type for x in src_files]

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

        self.render_template('vivado-project.tcl.j2',
                             self.name+'.tcl',
                             template_vars)

        self.render_template('vivado-makefile.j2',
                             'Makefile',
                             {'name' : self.name,
                              'part' : self.tool_options.get('part', ""),
                              'bitstream' : self.name+'.bit'})

        self.render_template('vivado-run.tcl.j2',
                             self.name+"_run.tcl")

        self.render_template('vivado-synth.tcl.j2',
                             self.name+"_synth.tcl")

        self.render_template('vivado-program.tcl.j2',
                             self.name+"_pgm.tcl")

    def src_file_filter(self, f):
        def _vhdl_source(f):
            s = 'read_vhdl'
            if f.file_type == 'vhdlSource-2008':
                s += ' -vhdl2008'
            if f.logical_name:
                s += ' -library '+f.logical_name
            return s

        file_types = {
            'verilogSource'       : 'read_verilog',
            'systemVerilogSource' : 'read_verilog -sv',
            'vhdlSource'          : _vhdl_source(f),
            'xci'                 : 'read_ip',
            'xdc'                 : 'read_xdc',
            'tclSource'           : 'source',
            'SDC'                 : 'read_xdc -unmanaged',
        }
        _file_type = f.file_type.split('-')[0]
        if _file_type in file_types:
            return file_types[_file_type] + ' ' + f.name
        elif _file_type == 'user':
            return ''
        else:
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name,
                                     f.file_type))
        return ''

    def build_main(self):
        logger.info("Building")
        args = []
        if 'pnr' in self.tool_options:
            if self.tool_options['pnr'] == 'vivado':
                pass
            elif self.tool_options['pnr'] == 'none':
                args.append('synth')
        self._run_tool('make', args)

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
