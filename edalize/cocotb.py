import logging
import os.path
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

# This is a list of simulators where VHDL libraries are supported in cocotb
sims_with_vhdl_lib_support = ['ghdl']
# Minor hack to deal with verilog include directories. Patching cocotb to do the
# simulator specifics maybe better long term. Basing this off cocotb
# axi-lite-slave example Makefile.
verilog_include_prefix = {'icarus': '-I', 'default': '+incdir+'}


class Cocotb(Edatool):

    argtypes = []

    makefile_template = 'cocotb-makefile.j2'

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description': 'cocotb - see <https://docs.cocotb.org/> for additional documentation on options',
                    'members': [
                        {'name': 'sim',
                         'type': 'String',
                         'desc': 'The simulator for Cocotb to use (required)'},
                        {'name': 'module',
                         'type': 'String',
                         'desc': 'Comma-separated list of the Python modules to search for test functions (required)'},
                        {'name': 'toplevel_lang',
                         'type': 'String',
                         'desc': 'Language of top level HDL module (required)'},
                        {'name': 'rtl_library',
                         'type': 'String',
                         'desc': 'VHDL library for top level entity'},
                        {'name': 'gui',
                         'type': 'String',
                         'desc': 'Set to 1 to enable GUI mode in simulator'},
                        {'name': 'waves',
                         'type': 'String',
                         'desc': 'Set to 1 to enable wave traces dump'},
                        {'name': 'compile_args',
                         'type': 'String',
                         'desc': 'Any arguments or flags to pass to the compile stage of the simulation'},
                        {'name': 'sim_args',
                         'type': 'String',
                         'desc': 'Any arguments or flags to pass to the execution of the compiled simulation'},
                        {'name': 'run_args',
                         'type': 'String',
                         'desc': 'Any argument to be passed to the “first” invocation of a simulator that runs via a TCL script'},
                        {'name': 'extra_args',
                         'type': 'String',
                         'desc': 'Passed to both the compile and execute phases of simulators with '
                                 'two rules, or passed to the single compile and run command for simulators '
                                 'which don’t have a distinct compilation stage'},
                        {'name': 'random_seed',
                         'type': 'String',
                         'desc': 'Seed the Python random module to recreate a previous test stimulus'},
                        {'name': 'testcase',
                         'type': 'String',
                         'desc': 'Comma-separated list the test functions to run'},
                        {'name': 'cocotb_results_file',
                         'type': 'String',
                         'desc': 'The file name where xUnit XML tests results are stored'},
                        ]}

    def _create_python_path(self):
        (src_files, incdirs) = self._get_fileset_files()
        path_components = []

        for f in src_files:
            if f.file_type == 'pythonSource':
                component = os.path.join('$(PWD)', os.path.dirname(f.name))
                if component not in path_components:
                    path_components.append(component)

        return ':'.join(path_components)

    def _get_sources(self):
        (src_files, incdirs) = self._get_fileset_files()
        verilog_sources = []
        vhdl_sources = []
        vhdl_lib_sources = {}

        use_vhdl_lib_sources = self.tool_options['sim'] in sims_with_vhdl_lib_support

        for f in src_files:
            path = os.path.join('$(PWD)', f.name)

            if f.file_type.startswith('vhdlSource'):
                if use_vhdl_lib_sources and f.logical_name:
                    if f.logical_name not in vhdl_lib_sources:
                        vhdl_lib_sources[f.logical_name] = []
                    vhdl_lib_sources[f.logical_name].append(path)
                else:
                    vhdl_sources.append(path)
            elif f.file_type.startswith('verilogSource'):
                verilog_sources.append(path)
            elif f.file_type.startswith('systemVerilogSource'):
                verilog_sources.append(path)

        joined_vhdl_lib_sources = {}
        for lib, sources in vhdl_lib_sources.items():
            joined_vhdl_lib_sources[lib] = ' '.join(sources)

        return ' '.join(verilog_sources), ' '.join(vhdl_sources), joined_vhdl_lib_sources

    def _get_verilog_include_args(self):
        (src_files, incdirs) = self._get_fileset_files()

        if self.tool_options['sim'] in verilog_include_prefix:
            prefix = verilog_include_prefix[self.tool_options['sim']]
        else:
            prefix = verilog_include_prefix['default']

        verilog_include_args = [prefix + os.path.join('$(PWD)', dir) for dir in incdirs]

        return ' '.join(verilog_include_args)

    def configure_main(self):
        python_path = self._create_python_path()
        (verilog_sources, vhdl_sources, vhdl_lib_sources) = self._get_sources()
        verilog_include_args = self._get_verilog_include_args()

        self.render_template(self.makefile_template, 'Makefile', {
            'verilog_sources': verilog_sources,
            'verilog_include_args': verilog_include_args,
            'vhdl_sources': vhdl_sources,
            'vhdl_lib_sources': vhdl_lib_sources,
            'python_path': python_path,
            'toplevel': self.toplevel,
            'tool_options': self.tool_options,
            })

    def build_main(self):
        pass

    def run_main(self):
        self._run_tool('make')
