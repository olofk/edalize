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


class Libero(Edatool):
    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description': "The Libero backend supports Microsemi Libero to build systems and program the FPGA",
                    'members': [
                        {'name': 'family',
                         'type': 'String',
                         'desc': 'FPGA family (e.g. PolarFire)'},
                        {'name': 'die',
                         'type': 'String',
                         'desc': 'FPGA device (e.g. MPF300TS)'},
                        {'name': 'package',
                         'type': 'String',
                         'desc': 'FPGA package type (e.g. FCG1152)'},
                        {'name': 'speed',
                         'type': 'String',
                         'desc': 'FPGA speed rating (e.g. -1)'},
                        {'name': 'dievoltage',
                         'type': 'String',
                         'desc': 'FPGA die voltage (e.g. 1.0)'},
                        {'name': 'range',
                         'type': 'String',
                         'desc': 'FPGA temperature range (e.g. IND)'},
                        {'name': 'defiostd',
                         'type': 'String',
                         'desc': 'FPGA default IO std (e.g. "LVCMOS 1.8V"'},
                        {'name': 'hdl',
                         'type': 'String',
                         'desc': 'Default HDL (e.g. "VERILOG"'}
                    ]
                    }

    argtypes = ['vlogdefine', 'vlogparam']

    tool_options_defaults = {
        'speed': '-1',
        'dievoltage': '1.0',
        'range': 'IND',
        'defiostd': 'LVCMOS 1.8V',
        'hdl': 'VERILOG',
    }

    def _set_tool_options_defaults(self):
        for key, default_value in self.tool_options_defaults.items():
            if not key in self.tool_options:
                logger.info("Set Libero tool option %s to default value %s"
                            % (key, str(default_value)))
                self.tool_options[key] = default_value

    """ Initial setup of the class

    This calls the parent constructor, but also identifies whether
    the current system is using a Standard or Pro edition of Quartus.
    """

    def __init__(self, edam=None, work_root=None, eda_api=None):
        if not edam:
            edam = eda_api

        super(Libero, self).__init__(edam, work_root)

    """ Configuration is the first phase of the build

    This writes the project TCL file. It first collects all
    sources, IPs and constraints and then writes them to the TCL file along
    with the build steps.
    """

    def configure_main(self):
        self._set_tool_options_defaults()
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters['src_file_filter'] = self.src_file_filter
        self.jinja_env.filters['pdc_file_filter'] = self.pdc_file_filter

        escaped_name = self.name.replace(".", "_")

        template_vars = {
            'name': escaped_name,
            'src_files': src_files,
            'incdirs': incdirs,
            'tool_options': self.tool_options,
            'toplevel': self.toplevel,
            'generic': self.generic,
            'prj_root': "../prj",
            'op': "{",
            'cl': "}"
        }

        # Render the TCL project file
        self.render_template('libero-project.tcl.j2',
                             escaped_name + '-project.tcl',
                             template_vars)

        # Render the TCL run file
        self.render_template('libero-run.tcl.j2',
                             escaped_name + '-run.tcl',
                             template_vars)

    def src_file_filter(self, f):
        file_types = {
            'PDC': '-io_pdc {',
        }
        _file_type = f.file_type.split('-')[0]
        if _file_type in file_types:
            return file_types[_file_type] + f.name
        return ''

    def pdc_file_filter(self, f):
        file_types = {
            'PDC': 'constraint/io/',
        }
        _file_type = f.file_type.split('-')[0]
        if _file_type in file_types:
            filename = f.name.split("/")[-1]
            return file_types[_file_type] + filename
        return ''

    def build_main(self):
        logger.info("Libero TCL Scripts generated.")

    def run_main(self):
        pass
