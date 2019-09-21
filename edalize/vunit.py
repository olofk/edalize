import os
import sys
import logging
from functools import partial
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Vunit(Edatool):
    argtypes = ['cmdlinearg']
    testrunner_template = "run.py.j2"
    testrunner = "run.py"

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description': "VUnit testing framework",
                    'lists': [
                        {'name': 'vunit_options',
                         'type': 'String',
                         'desc': 'Options to pass to the VUnit test runner'}]}

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters['src_file_filter'] = self.src_file_filter

        library_names = [f.logical_name for f in src_files]

        # vunit does not allow empty library name or 'work', so we use `vunit_test_runner`:
        libraries = {lib if lib != '' else 'vunit_test_runner': [
            file for file in src_files if file.logical_name == lib] for lib in library_names}

        escaped_name = self.name.replace(".", "_")

        self.render_template(self.testrunner_template,
                             self.testrunner,
                             {'name': escaped_name,
                              'libraries': libraries,
                              'tool_options': self.tool_options})

    def run_main(self):
        vunit_options = self.tool_options.get('vunit_options', [])
        _vsim_options = self.tool_options.get('vsim_options', [])
        testrunner = os.path.join(self.work_root, self.testrunner)
        self._run_tool(sys.executable, [testrunner] + vunit_options)

    def build_main(self):
        pass

    def src_file_filter(self, f):
        def _handle_src(t, f):
            return f.name

        def _get_file_type(f):
            return f.file_type.split('-')[0]

        file_mapping = {
            'verilogSource': partial(_handle_src,  'VERILOG_FILE'),
            'systemVerilogSource': partial(_handle_src,  'SYSTEMVERILOG_FILE'),
            'vhdlSource': partial(_handle_src,  'VHDL_FILE'),
        }

        _file_type = _get_file_type(f)
        if _file_type in file_mapping:
            return file_mapping[_file_type](f)
        elif _file_type == 'user':
            return ''
        else:
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name,
                                     f.file_type))

        return ''
