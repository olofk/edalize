import logging
import re
import os
import subprocess

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Veriblelint(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Verible lint backend (verilog_lint)",
                    'members': [
                         {'name': 'ruleset',
                          'type': 'String',
                          'desc': 'Ruleset: [default|all|none]'},
                    ],
                    'lists': [
                         {'name' : 'verible_lint_args',
                         'type' : 'String',
                         'desc' : 'Extra command line arguments passed to the Verible tool'},
                         {'name': 'rules',
                          'type': 'String',
                          'desc': 'What rules to use. Prefix a rule name with "-" to disable it.'},
                    ]}


    def build_main(self):
        pass

    def _get_tool_args(self):
        args = [ '--lint_fatal', '--parse_fatal' ]

        if 'rules' in self.tool_options:
            args.append('--rules=' + ','.join(self.tool_options['rules']))
        if 'ruleset' in self.tool_options:
            args.append('--ruleset=' + self.tool_options['ruleset'])
        if 'verible_lint_args' in self.tool_options:
            args += self.tool_options['verible_lint_args']

        return args

    def run_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        src_files_filtered = []
        config_files_filtered = []
        for src_file in src_files:
            ft = src_file.file_type

            if ft.startswith("verilogSource") or ft.startswith("systemVerilogSource"):
               src_files_filtered.append(src_file.name)
            elif ft.startswith("veribleLintRules"):
               config_files_filtered.append(src_file.name)

        if len(src_files_filtered) == 0:
            logger.warning("No SystemVerilog source files to be processed.")
            return

        lint_fail = False
        args = self._get_tool_args()
        if len(config_files_filtered) > 1:
            raise RuntimeError("Too many Verible lint rule files specified")
        elif len(config_files_filtered) == 1:
            args.append('--rules_config=' + config_files_filtered[0])

        for src_file in src_files_filtered:
            cmd = ['verilog_lint'] + args + [src_file]
            logger.debug("Running " + ' '.join(cmd))

            try:
                res = subprocess.run(cmd, cwd = self.work_root, check=False)
            except FileNotFoundError:
                _s = "Command '{}' not found. Make sure it is in $PATH"
                raise RuntimeError(_s.format(cmd[0]))

            if res.returncode != 0:
                lint_fail = True
        if lint_fail:
            raise RuntimeError("Lint failed")
