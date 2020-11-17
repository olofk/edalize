import logging
import os.path
import os
import platform
import subprocess
import re
import xml.etree.ElementTree as ET
from functools import partial
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Quartus(Edatool):

    argtypes = ['vlogdefine', 'vlogparam', 'generic']

    # Define Standard edition to be our default version
    isPro = False
    makefile_template = {False : "quartus-std-makefile.j2",
                         True  : "quartus-pro-makefile.j2"}

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "The Quartus backend supports Intel Quartus Std and Pro editions to build systems and program the FPGA",
                    'members' : [
                        {'name' : 'family',
                         'type' : 'String',
                         'desc' : 'FPGA family (e.g. Cyclone V)'},
                        {'name' : 'device',
                         'type' : 'String',
                         'desc' : 'FPGA device (e.g. 5CSXFC6D6F31C8ES)'},
                        {'name' : 'cable',
                         'type' : 'String',
                         'desc' : "Specifies the FPGA's JTAG programming cable. Use the tool `jtagconfig` to determine the available cables."},
                        {'name' : 'board_device_index',
                         'type' : 'String',
                         'desc' : "Specifies the FPGA's device number in the JTAG chain. The device index specifies the device where the flash programmer looks for the Nios® II JTAG debug module. JTAG devices are numbered relative to the JTAG chain, starting at 1. Use the tool `jtagconfig` to determine the index."},
                        {'name' : 'pnr',
                         'type' : 'String',
                         'desc' : 'P&R tool. Allowed values are quartus (default), dse (to run Design Space Explorer) and none (to just run synthesis)'}],
                    'lists' : [
                        {'name' : 'dse_options',
                         'type' : 'String',
                         'desc' : 'Options for DSE (Design Space Explorer)'},
                        {'name' : 'quartus_options',
                         'type' : 'String',
                         'desc' : 'Additional options for Quartus'},
                        ]}
    """ Initial setup of the class

    This calls the parent constructor, but also identifies whether
    the current system is using a Standard or Pro edition of Quartus.
    """
    def __init__(self, edam=None, work_root=None, eda_api=None):
        if not edam:
            edam = eda_api

        super(Quartus, self).__init__(edam, work_root)

        # Acquire quartus_sh identification information from available tool if
        # possible. We always default to version 18.1 Standard if a problem is encountered
        version = {
            'major':   '18',
            'minor':   '1',
            'patch':   '0',
            'date':    '01/01/2019',
            'edition': 'Standard'
        }
        try:
            qsh_text = subprocess.Popen(["quartus_sh", "--version"], stdout=subprocess.PIPE, env=os.environ).communicate()[0]

            # Attempt to pattern match the output. Examples include
            # Version 16.1.2 Build 203 01/18/2017 SJ Standard Edition
            # Version 17.1.2 Build 304 01/31/2018 SJ Pro Edition
            version_exp = r'Version (?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+) ' + \
                          r'Build (?P<build>\d+) (?P<date>\d{2}/\d{2}/\d{4}) (?:\w+) '    + \
                          r'(?P<edition>(Lite|Standard|Pro)) Edition'

            match = re.search(version_exp, str(qsh_text))
            if match != None:
                version = match.groupdict()
        except:
            # It is possible for this to have been run on a box without
            # Quartus being installed. Allow these errors to be ignored
            logger.warning("Unable to recognise Quartus version via quartus_sh")

        self.isPro = (version['edition'] == "Pro")

        # Quartus Pro 17 and later use 1/0 for boolean generics. Other editions
        # and versions use "true"/"false" strings
        if (version['edition'] != "Pro") or (int(version['major']) < 17):
            self.jinja_env.filters['generic_value_str'] = \
                partial(self.jinja_env.filters['generic_value_str'], bool_is_str=True)

    """ Configuration is the first phase of the build

    This writes the project TCL files and Makefile. It first collects all
    sources, IPs and constraints and then writes them to the TCL file along
    with the build steps.
    """
    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters['src_file_filter'] = self.src_file_filter
        self.jinja_env.filters['qsys_file_filter'] = self.qsys_file_filter

        has_vhdl2008 = 'vhdlSource-2008' in [x.file_type for x in src_files]
        has_qsys     = 'QSYS'            in [x.file_type for x in src_files]

        escaped_name = self.name.replace(".", "_")

        template_vars = {
            'name'         : escaped_name,
            'src_files'    : src_files,
            'incdirs'      : incdirs,
            'tool_options' : self.tool_options,
            'toplevel'     : self.toplevel,
            'vlogparam'    : self.vlogparam,
            'vlogdefine'   : self.vlogdefine,
            'generic'      : self.generic,
            'has_vhdl2008' : has_vhdl2008
        }

        # Render Makefile based on detected version
        self.render_template(self.makefile_template[self.isPro],
                             'Makefile',
                             { 'name'         : escaped_name,
                               'src_files'    : src_files,
                               'tool_options' : self.tool_options})

        # Render the TCL project file
        self.render_template('quartus-project.tcl.j2',
                             escaped_name + '.tcl',
                             template_vars)


    # Helper to extract file type
    def file_type(self, f):
        return f.file_type.split('-')[0]

    # Filter for just QSYS files. This verifies that they are compatible
    # with the identified Quartus version
    def qsys_file_filter(self, f):
        name = ''
        if self.file_type(f) == 'QSYS':
            # Compatibility checks
            try:
                qsysTree = ET.parse(os.path.join(self.work_root, f.name))
                try:
                    tool = qsysTree.find('component').attrib['tool']
                    if tool == 'QsysPro' and self.isPro:
                        name = f.name
                except (AttributeError, KeyError):
                    # Either a component wasn't found in the QSYS file, or it
                    # had no associated tool information. Make the assumption
                    # it was a Standard edition file
                    if not self.isPro:
                        name = f.name
            except (ET.ParseError, IOError):
                logger.warning("Unable to parse QSYS file " + f.name)

            # Give QSYS files special attributes to make the logic in
            # the Jinja2 templates much simplier
            setattr(f, "simplename", os.path.basename(f.name).split('.qsys')[0])
            setattr(f, "srcdir", os.path.dirname(f.name) or '.')
            setattr(f, "dstdir", os.path.join('qsys', f.simplename))
        
        return name

    # Allow the templates to get source file information
    def src_file_filter(self, f):
        def _append_library(f):
            s = ""
            if f.logical_name:
                s += ' -library ' + f.logical_name
            return s

        def _handle_qsys(t, f):
            # Quartus Pro just passes QSYS files onto the compiler, but Standard
            # expects to see them sepecified as QIP. The Makefile is responsible
            # for creating that QIP file for Standard edition in a known place
            # which can be used below
            if self.isPro:
                return _handle_src(t, f)
            else:
                f.name = os.path.join(f.dstdir, f.simplename + '.qip')
                f.file_type = 'QIP'
                return _handle_src('QIP_FILE', f)

        def _handle_src(t, f):
            s = 'set_global_assignment -name ' + t
            s += _append_library(f)
            s += ' ' + f.name
            return s

        def _handle_tcl(f):
            return "source " + f.name

        file_mapping = {
            'verilogSource'       : partial(_handle_src,  'VERILOG_FILE'),
            'systemVerilogSource' : partial(_handle_src,  'SYSTEMVERILOG_FILE'),
            'vhdlSource'          : partial(_handle_src,  'VHDL_FILE'),
            'SDC'                 : partial(_handle_src,  'SDC_FILE'),
            'QSYS'                : partial(_handle_qsys, 'QSYS_FILE'),
            'QIP'                 : partial(_handle_src,  'QIP_FILE'),
            'IP'                  : partial(_handle_src,  'IP_FILE'),
            'tclSource'           : partial(_handle_tcl),
        }

        _file_type = self.file_type(f)
        if _file_type in file_mapping:
            return file_mapping[_file_type](f)
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
            if self.tool_options['pnr'] == 'quartus':
                pass
            elif self.tool_options['pnr'] == 'dse':
                args.append('dse')
            elif self.tool_options['pnr'] == 'none':
                args.append('syn')
        self._run_tool('make', args, quiet=True)

    """ Program the FPGA
    """
    def run_main(self):
        args = ['--mode=jtag']
        if 'cable' in self.tool_options:
            args += ['-c', self.tool_options['cable']]
        args += ['-o']
        args += ['p;' + self.name.replace('.', '_') + '.sof']

        if 'pnr' in self.tool_options:
            if self.tool_options['pnr'] == 'quartus':
                pass
            elif self.tool_options['pnr'] == 'dse':
                return
            elif self.tool_options['pnr'] == 'none':
                return

        if 'board_device_index' in self.tool_options:
            args[-1] += "@" + self.tool_options['board_device_index']

        self._run_tool('quartus_pgm', args)
