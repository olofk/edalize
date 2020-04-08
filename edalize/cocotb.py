import logging
import os.path
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Cocotb(Edatool):

    argtypes = []

    makefile_template = 'cocotb-makefile.j2'

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Cocotb",
                    'lists' : [
                        {'name': 'sim',
                         'type': 'String',
                         'desc': 'The simulator for Cocotb to use'},
                        {'name': 'module',
                         'type': 'String',
                         'desc': 'Name of top level Python testbench'},
                        {'name': 'toplevel_lang',
                         'type': 'String',
                         'desc': 'Language of top level HDL module'},
                        ]}

    def _create_python_path(self):
        (src_files, incdirs) = self._get_fileset_files()
        path_components = []

        for f in src_files:
            if f.file_type == 'pythonSource':
                component = os.path.dirname(f.name)
                if component != '' and component not in path_components:
                    path_components.append(component)
                    
        return ':'.join(path_components)

    def _get_sources(self):
        (src_files, incdirs) = self._get_fileset_files()
        verilog_sources = []
        vhdl_sources = []

        for f in src_files:
            if f.file_type.startswith('vhdlSource'):
                vhdl_sources.append(f.name)
            elif f.file_type.startswith('verilogSource'):
                verilog_sources.append(f.name)
            elif f.file_type.startswith('systemVerilogSource'):
                verilog_sources.append(f.name)

        return verilog_sources, vhdl_sources

    def configure_main(self):
        python_path = self._create_python_path()
        (verilog_sources, vhdl_sources) = self._get_sources()
        self.render_template(self.makefile_template, 'Makefile', {
            'verilog_sources': ' '.join(verilog_sources),
            'vhdl_sources': ' '.join(vhdl_sources),
            'python_path': python_path,
            'toplevel': self.toplevel,
            'sim': self.tool_options['sim'][0],
            'module': self.tool_options['module'][0],
            'toplevel_lang': self.tool_options['toplevel_lang'][0],
            })

    def build_main(self):
        pass

    def run_main(self):
        self._run_tool('make')