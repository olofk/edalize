import logging
import os
import pathlib

import cocotb

from edalize import get_edatool

logger = logging.getLogger(__name__)


# This class could be replaced by calls to cocotb-config. Knowledge of these
# simulator arguments belongs in the cocotb codebase.
class CocotbConfig:

    @staticmethod
    def get_simulator_args(simulator, toplevel_lang):
        if simulator == 'ghdl':
            return CocotbConfig.get_ghdl_args(toplevel_lang)
        elif simulator == 'icarus':
            return CocotbConfig.get_icarus_args(toplevel_lang)
        else:
            raise RuntimeError('Simulator ' + simulator + ' is not supported by cocotb backend')

    @staticmethod
    def get_ghdl_args(toplevel_lang):
        if toplevel_lang != 'vhdl':
            raise RuntimeError('GHDL only supports VHDL')

        ghdl_cocotb_lib = pathlib.Path(os.path.dirname(cocotb.__file__)) / 'libs' / 'libcocotbvpi_ghdl.so'

        return [f"--vpi={ghdl_cocotb_lib}"]

    @staticmethod
    def get_icarus_args(toplevel_lang):
        if toplevel_lang != 'verilog':
            raise RuntimeError('Icarus only supports Verilog')

        cocotb_lib_dir = pathlib.Path(os.path.dirname(cocotb.__file__)) / 'libs'

        return ['-M', str(cocotb_lib_dir), '-m', 'libcocotbvpi_icarus']


# Don't inherit from Edatool so we can delegate methods to simulator backend with getattr
class Cocotb:

    argtypes = []

    # Name of tool_option where cocotb library arguments are added
    option_name = {
        'ghdl': 'run_options',
        'icarus': 'vpp_options'
    }

    # Delegate undefined calls to wrapped simulator
    def __getattr__(self, k):
        return getattr(self.simulator, k)

    def __init__(self, edam=None, work_root=None, eda_api=None):
        _tool_name = self.__class__.__name__.lower()

        if not edam:
            edam = eda_api

        self.tool_options = edam.get('tool_options', {}).pop(_tool_name, {})
        self.work_root = work_root

        try:
            simulator_name = self.tool_options['simulator']
        except KeyError:
            raise RuntimeError("Missing required parameter 'simulator' in cocotb options")

        try:
            toplevel_lang = self.tool_options['toplevel_lang']
        except KeyError:
            raise RuntimeError("Missing required parameter 'toplevel_lang' in cocotb options")

        # Add options to edam for simulator backend
        cocotb_args = CocotbConfig.get_simulator_args(simulator_name, toplevel_lang)
        simulator_options = self.tool_options.get('tool_options', {})
        if self.option_name[simulator_name] in simulator_options:
            simulator_options[self.option_name[simulator_name]] += cocotb_args
        else:
            simulator_options[self.option_name[simulator_name]] = cocotb_args

        edam['tool_options'][simulator_name] = simulator_options

        # Instantiate the required simulator backend
        self.simulator = get_edatool(simulator_name)(edam, work_root)

        # Run methods that rely on delegation to simulator backend
        extra_env = self._create_environment()
        self.simulator.env.update(extra_env)

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description': 'cocotb - see <https://docs.cocotb.org/> for additional documentation on options',
                    'members': [
                        {'name': 'simulator',
                         'type': 'String',
                         'desc': 'The simulator backend to use to run Cocotb (required)'},
                        {'name': 'module',
                         'type': 'String',
                         'desc': 'Comma-separated list of the Python modules to search for test functions (required)'},
                        {'name': 'toplevel_lang',
                         'type': 'String',
                         'desc': 'Language of top level HDL module (required)'},
                        {'name': 'random_seed',
                         'type': 'Integer',
                         'desc': 'Seed the Python random module to recreate a previous test stimulus'},
                        {'name': 'testcase',
                         'type': 'String',
                         'desc': 'Comma-separated list the test functions to run'},
                        {'name': 'cocotb_results_file',
                         'type': 'String',
                         'desc': 'The file name where xUnit XML tests results are stored'},
                    ]
                    }

    # This creates a python path that contains the parent directory of every
    # python file in the fileset. This is not ideal because several directories
    # in a hierarchical tree may be added, which allows a given module to be
    # imported in several ways. One way to fix this in future might be to allow
    # path components to be passed into Edalize from FuseSoC as well as files.
    def _create_python_path(self):
        (src_files, incdirs) = self._get_fileset_files()
        path_components = []

        for f in src_files:
            if f.file_type == 'pythonSource':
                component = os.path.join(self.work_root, os.path.dirname(f.name))
                if component not in path_components:
                    path_components.append(component)

        return os.pathsep.join(path_components)

    def _create_environment(self):
        extra_env = {}

        extra_env['MODULE'] = self.tool_options['module']
        extra_env['TOPLEVEL_LANG'] = self.tool_options['toplevel_lang']

        pythonpath = self._create_python_path()

        if 'PYTHONPATH' in os.environ:
            extra_env['PYTHONPATH'] += os.pathsep + pythonpath
        else:
            extra_env['PYTHONPATH'] = pythonpath

        if 'random_seed' in self.tool_options:
            extra_env['RANDOM_SEED'] = str(self.tool_options['random_seed'])

        if 'testcase' in self.tool_options:
            extra_env['TESTCASE'] = self.tool_options['testcase']

        if 'cocotb_results_file' in self.tool_options:
            extra_env['COCOTB_RESULTS_FILE'] = self.tool_options['cocotb_results_file']

        return extra_env
