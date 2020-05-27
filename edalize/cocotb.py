import logging
import os

from edalize.helpers.cocotb_args import get_cocotb_args

from edalize import get_edatool
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Cocotb(Edatool):

    argtypes = []

    def __init__(self, edam=None, work_root=None, eda_api=None):
        _tool_name = self.__class__.__name__.lower()

        if not edam:
            edam = eda_api
        try:
            self.name = edam['name']
        except KeyError:
            raise RuntimeError("Missing required parameter 'name'")

        self.tool_options = edam.get('tool_options', {}).pop(_tool_name, {})
        self.files = edam.get('files', [])
        self.work_root = work_root

        try:
            simulator_name = self.tool_options['sim']
        except KeyError:
            raise RuntimeError("Missing required parameter 'sim' in cocotb options")

        try:
            toplevel_lang = self.tool_options['toplevel_lang']
        except KeyError:
            raise RuntimeError("Missing required parameter 'toplevel_lang' in cocotb options")

        # Add options to edam for simulator backend
        (option_name, args) = get_cocotb_args(simulator_name, toplevel_lang)
        simulator_options = self.tool_options.get('tool_options', {})
        if option_name in simulator_options:
            simulator_options[option_name] += [args]
        else:
            simulator_options[option_name] = [args]

        edam['tool_options'][simulator_name] = simulator_options

        self._configure_environment()

        # Instantiate the required simulator backend
        self.simulator = get_edatool(simulator_name)(edam, work_root)

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description': 'cocotb - see <https://docs.cocotb.org/> for additional documentation on options',
                    'members': [
                        {'name': 'sim',
                         'type': 'String',
                         'desc': 'The simulator to use(required)'},
                        {'name': 'module',
                         'type': 'String',
                         'desc': 'Comma-separated list of the Python modules to search for test functions (required)'},
                        {'name': 'toplevel_lang',
                         'type': 'String',
                         'desc': 'Language of top level HDL module (required)'},
                        {'name': 'random_seed',
                         'type': 'String',
                         'desc': 'Seed the Python random module to recreate a previous test stimulus'},
                        {'name': 'testcase',
                         'type': 'String',
                         'desc': 'Comma-separated list the test functions to run'},
                        {'name': 'cocotb_results_file',
                         'type': 'String',
                         'desc': 'The file name where xUnit XML tests results are stored'},
                        ]
                    }

    def _create_python_path(self):
        (src_files, incdirs) = self._get_fileset_files()
        path_components = []

        for f in src_files:
            if f.file_type == 'pythonSource':
                component = os.path.join(self.work_root, os.path.dirname(f.name))
                if component not in path_components:
                    path_components.append(component)

        return ':'.join(path_components)

    def _configure_environment(self):
        os.environ['MODULE'] = self.tool_options['module']
        os.environ['TOPLEVEL_LANG'] = self.tool_options['toplevel_lang']

        pythonpath = self._create_python_path()

        if 'PYTHONPATH' in os.environ:
            os.environ['PYTHONPATH'] += ':' + pythonpath
        else:
            os.environ['PYTHONPATH'] = pythonpath

    # Delegate all configure, build and run methods to simulator object

    def configure_pre(self):
        self.simulator.configure_pre()

    def configure_main(self):
        self.simulator.configure_main()

    def configure_post(self):
        self.simulator.configure_post()

    def build_pre(self):
        self.simulator.build_pre()

    def build_main(self, target=None):
        self.simulator.build_main(target)

    def build_post(self):
        self.simulator.build_post()

    def run_pre(self, args=None):
        self.simulator.run_pre(args)

    def run_main(self):
        self.simulator.run_main()

    def run_post(self):
        self.simulator.run_post()
