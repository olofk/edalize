import os
import sys
import logging
from collections import OrderedDict
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Vunit(Edatool):
    argtypes = ["cmdlinearg"]
    testrunner_template = "run.py.j2"
    testrunner = "run.py"

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "VUnit testing framework",
                "members": [
                    {
                        "name": "vunit_runner",
                        "type": "String",
                        "desc": 'Name of the Python file exporting a "VUnitRunner" class that is used to configure and execute test',
                    }
                ],
                "lists": [
                    {
                        "name": "add_libraries",
                        "type": "String",
                        "desc": 'A list of framework libraries to add. Allowed values include "array_util", "com", "json4hdl", "osvvm", "random", "verification_components"',
                    },
                    {
                        "name": "vunit_options",
                        "type": "String",
                        "desc": "Options to pass to the VUnit test runner",
                    },
                ],
            }

    def get_vunit_runner_path(self, src_files):
        # TODO: Figure out a better way to get the path to the runner
        runner = self.tool_options.get("vunit_runner", "")
        if len(runner) == 0:
            return ""
        for f in src_files:
            if f.name.endswith(runner):
                return f.name
        return ""

    def configure_main(self):
        (src_files, _incdirs) = self._get_fileset_files(force_slash=True)
        self.jinja_env.filters["src_file_filter"] = self.src_file_filter
        self.jinja_env.filters[
            "src_file_vhdl_standard_filter"
        ] = self.src_file_vhdl_standard_filter

        # vunit does not allow empty library name or 'work', so we use `vunit_test_runner_lib`:
        libraries = OrderedDict()

        for f in src_files:
            lib = f.logical_name if f.logical_name else "vunit_test_runner_lib"

            if lib in libraries:
                libraries[lib].append(f)
            else:
                libraries[lib] = [f]

        escaped_name = self.name.replace(".", "_")
        add_libraries = self.tool_options.get("add_libraries", [])
        self.render_template(
            self.testrunner_template,
            self.testrunner,
            {
                "name": escaped_name,
                "vunit_runner_path": self.get_vunit_runner_path(src_files),
                "libraries": libraries,
                "add_libraries": add_libraries,
                "tool_options": self.tool_options,
            },
        )

    def build_main(self):
        vunit_options = self.tool_options.get("vunit_options", [])
        testrunner = os.path.join(self.work_root, self.testrunner)
        self._run_tool(sys.executable, [testrunner, "--compile", "-k"] + vunit_options, quiet=True)

    def run_main(self):
        vunit_options = self.tool_options.get("vunit_options", [])
        testrunner = os.path.join(self.work_root, self.testrunner)
        self._run_tool(sys.executable, [testrunner] + vunit_options)

    def src_file_vhdl_standard_filter(self, f):
        fragments = f.file_type.split("-")
        if fragments[0] != "vhdlSource" or len(fragments) < 2:
            return ""
        return fragments[1]

    def src_file_filter(self, f):
        def _get_file_type(f):
            return f.file_type.split("-")[0]

        file_mapping = {
            "verilogSource": lambda f: f.name,
            "systemVerilogSource": lambda f: f.name,
            "vhdlSource": lambda f: f.name,
        }

        _file_type = _get_file_type(f)
        if _file_type in file_mapping:
            return file_mapping[_file_type](f)
        elif _file_type == "user":
            return ""
        elif _file_type != "pythonSource":
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f.name, f.file_type))

        return ""
