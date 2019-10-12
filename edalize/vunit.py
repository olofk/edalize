import os
import sys
import logging
from shutil import copy
from os.path import splitext
from functools import partial
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Vunit(Edatool):
    argtypes = ['cmdlinearg']
    testrunner_template = "run.py.j2"
    testrunner = "run.py"
    vunit_hooks_template = 'vunit_hooks.py.j2'
    vunit_hooks = 'vunit_hooks.py'

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description': "VUnit testing framework",
                    'members' : [
                        {'name': 'vunit_runner',
                         'type': 'String',
                         'desc': 'Name of the Python file exporting a "VUnitRunner" class that is used to configure and execute test'}],
                    'lists': [
                        {'name': 'add_libraries',
                         'type': 'String',
                         'desc': 'A list of framework libraries to add. Allowed values include "array_util", "com", "json4hdl", "osvvm", "random", "verification_components"' },
                        {'name': 'vunit_options',
                         'type': 'String',
                         'desc': 'Options to pass to the VUnit test runner'}
                         ]}

    def _get_vunit_runner_name(self, src_files):
        vunit_runner_filename = self.tool_options.get('vunit_runner', None)
        if vunit_runner_filename is None:
            # if no vunit_runner.py exists, fall back to VUnitRunner from unit_hooks
            return 'vunit_hooks', None

        for f in src_files:
            if f.name.endswith(vunit_runner_filename):
                return splitext(vunit_runner_filename)[0], os.path.join(self.work_root, f.name)

        raise RuntimeError("Could not find specified test runner " + vunit_runner_filename + " in the files " + str(src_files))

    def configure_main(self):
        (src_files, _incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters['src_file_filter'] = self.src_file_filter

        library_names = [f.logical_name for f in src_files]

        # vunit does not allow empty library name or 'work', so we use `vunit_test_runner_lib`:
        libraries = {lib if lib != '' else 'vunit_test_runner_lib': [
            file for file in src_files if file.logical_name == lib] for lib in library_names}

        vunit_runner_name, vunit_runner_file = self._get_vunit_runner_name(src_files)
        if vunit_runner_file is not None:
            copy(vunit_runner_file, self.work_root)

        self.render_template(self.vunit_hooks_template,
                             self.vunit_hooks, {})

        escaped_name = self.name.replace(".", "_")
        add_libraries = self.tool_options.get('add_libraries', [])
        self.render_template(self.testrunner_template,
                             self.testrunner,
                             {'name': escaped_name,
                              'work_root': self.work_root,
                              'vunit_runner_name': vunit_runner_name,
                              'libraries': libraries,
                              'add_libraries': add_libraries,
                              'tool_options': self.tool_options})


    def run_main(self):
        vunit_options = self.tool_options.get('vunit_options', [])
        testrunner = os.path.join(self.work_root, self.testrunner)
        self._run_tool(sys.executable, [testrunner] + vunit_options)

    def build_main(self):
        pass

    def src_file_filter(self, f):
        def _get_file_type(f):
            return f.file_type.split('-')[0]

        file_mapping = {
            'verilogSource': lambda f: f.name,
            'systemVerilogSource': lambda f: f.name,
            'vhdlSource': lambda f: f.name
        }

        _file_type = _get_file_type(f)
        if _file_type in file_mapping:
            return file_mapping[_file_type](f)
        elif _file_type == 'user':
            return ''
        elif _file_type != 'pythonSource':
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name,
                                     f.file_type))

        return ''
