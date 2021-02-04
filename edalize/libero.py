import logging
import os
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

    mandatory_options = ['family', 'die', 'package', 'range']

    tool_options_defaults = {
        'range': 'IND',
        'hdl': 'VERILOG',
    }

    def _set_tool_options_defaults(self):
        for key, default_value in self.tool_options_defaults.items():
            if not key in self.tool_options:
                logger.info("Set Libero tool option %s to default value %s"
                            % (key, str(default_value)))
                self.tool_options[key] = default_value

    def _check_mandatory_options(self):
        shouldExit = 0
        for key in self.mandatory_options:
            if not key in self.tool_options:
                logger.error("Libero option \"%s\" must be defined", key)
                shouldExit = 1
        if shouldExit:
            exit(1)

    """ Configuration is the first phase of the build

    This writes the project TCL file. It first collects all
    sources, IPs and constraints and then writes them to the TCL file along
    with the build steps.
    """

    def configure_main(self):
        self._set_tool_options_defaults()
        self._check_mandatory_options()
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters['src_file_filter'] = self.src_file_filter
        self.jinja_env.filters['pdc_file_filter'] = self.pdc_file_filter

        escaped_name = self.name.replace(".", "_")

        template_vars = {
            'name': escaped_name,
            'src_files': src_files,
            'incdirs': incdirs,
            'vlogparam': self.vlogparam,
            'vlogdefine': self.vlogdefine,
            'tool_options': self.tool_options,
            'toplevel': self.toplevel,
            'generic': self.generic,
            'prj_root': "./prj",
            'op': "{",
            'cl': "}",
            'sp': " "
        }

        # Render the TCL project file
        self.render_template('libero-project.tcl.j2',
                             escaped_name + '-project.tcl',
                             template_vars)

        # Render the TCL run file
        self.render_template('libero-run.tcl.j2',
                             escaped_name + '-run.tcl',
                             template_vars)

        # Render the Synthesize TCL file
        self.render_template('libero-syn-user.tcl.j2',
                             escaped_name + '-syn-user.tcl',
                             template_vars)

        logger.info("Cores and Libero TCL Scripts generated.")

    def src_file_filter(self, f):
        file_types = {
            'verilogSource': '-hdl_source {',
            'systemVerilogSource': '-hdl_source {',
            'vhdlSource': "-hdl_source {",
            'PDC': '-io_pdc {',
            'SDC': '-sdc {',
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
        logger.info("Executing Libero TCL Scripts.")
        escaped_name = self.name.replace(".", "_")
        self._run_tool('libero', ['SCRIPT:' + escaped_name + '-project.tcl'])
        self._run_tool('libero', ['SCRIPT:' + escaped_name + '-run.tcl'])

    def run_main(self):
        pass
