# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands


class Verible(Edatool):
    description = "Verible lint (verible-verilog-lint)"

    TOOL_OPTIONS = {
        "ruleset": {
            "type": "str",
            "desc": "Ruleset: [default|all|none]",
        },
        "rules": {
            "type": "str",
            "desc": 'What rules to use. Prefix a rule name with "-" to disable it.',
            "list": True,
        },
        "verible_lint_args": {
            "type": "str",
            "desc": "Additional arguments passed to verible-verilog-lint",
            "list": True,
        },
        "lint_fatal": {
            "type": "bool",
            "desc": "Return a non-zero exit code for lint findings",
        },
        "parse_fatal": {
            "type": "bool",
            "desc": "Return a non-zero exit code for parse errors",
        },
    }

    def setup(self, edam):
        super().setup(edam)

        raw_args = self.tool_options.get("verible_lint_args", [])
        for raw_arg in raw_args:
            for option in ("lint_fatal", "parse_fatal"):
                if (
                    raw_arg == f"--{option}"
                    or raw_arg.startswith(f"--{option}=")
                    or raw_arg == f"--no{option}"
                ):
                    raise RuntimeError(
                        f"'{raw_arg}' conflicts with Verible's fatality controls. "
                        "Use the lint_fatal and parse_fatal boolean tool options instead."
                    )

        src_files = []
        rules_files = []
        waiver_files = []
        unused_files = []
        depfiles = []

        for f in self.files:
            file_type = f.get("file_type", "")
            if file_type.startswith("verilogSource") or file_type.startswith(
                "systemVerilogSource"
            ):
                depfiles.append(f["name"])
                if f.get("is_include_file"):
                    unused_files.append(f)
                else:
                    src_files.append(f["name"])
            elif file_type == "veribleLintRules":
                rules_files.append(f["name"])
                depfiles.append(f["name"])
            elif file_type == "veribleLintWaiver":
                waiver_files.append(f["name"])
                depfiles.append(f["name"])
            else:
                unused_files.append(f)

        if not src_files:
            raise RuntimeError(
                "verible needs at least one (System)Verilog source file to lint"
            )
        if len(rules_files) > 1:
            raise RuntimeError(
                "Verible lint only supports a single rules file (type veribleLintRules)"
            )

        self.edam = edam.copy()
        self.edam["files"] = unused_files

        lint_fatal = self.tool_options.get("lint_fatal", True)
        parse_fatal = self.tool_options.get("parse_fatal", True)
        args = [
            "--lint_fatal=" + self._param_value_str(lint_fatal, bool_is_str=True),
            "--parse_fatal=" + self._param_value_str(parse_fatal, bool_is_str=True),
        ]

        if "rules" in self.tool_options:
            args.append("--rules=" + ",".join(self.tool_options["rules"]))
        if "ruleset" in self.tool_options:
            args.append("--ruleset=" + self.tool_options["ruleset"])
        args += raw_args
        if rules_files:
            args.append("--rules_config=" + rules_files[0])
        if waiver_files:
            args.append("--waiver_files=" + ",".join(waiver_files))

        commands = EdaCommands()
        commands.add([], [".PHONY"], ["lint"])
        commands.add(
            ["verible-verilog-lint"] + args + src_files,
            ["lint"],
            depfiles,
        )
        commands.set_default_target("lint")
        self.commands = commands
