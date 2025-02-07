import os
import re

from collections import OrderedDict
from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands, get_file_type


from pathlib import Path

from edalize.tools.edatool import Edatool
from edalize.utils import EdaCommands

class Spyglass(Edatool):
    description = "Spyglass: Perform static source code analysis on HDL code"

    TOOL_OPTIONS = {
        "methodology": {
            "type": "str",
            "desc": "Path to methodology description",
        },
        "goals": {
            "type": "str",
            "desc": "Goals to run in Spyglass",
            "list": True,
        },
        "goal_options": {
            "type": "str",
            "desc": "Options for specific goals",
            "list": True,
        },
        "spyglass_options": {
            "type": "str",
            "desc": "Additional Spyglass options",
            "list": True,
        },
        "rule_parameters": {
            "type": "str",
            "desc": "Rule parameters for linting checks",
            "list": True,
        },
        "version" : {
            "type": "str",
            "desc": "Version of Spyglass", 
        },
    }

    def setup(self, edam):
        super().setup(edam)
        if not self.tool_options["version"]:
            raise RuntimeError("Tool 'SPYGLASS' requires tool option 'version' to be set, e.g. 2023_12")
        
        # ----------------- Prepare .prj ------------------------------------------#
    # Spyglass options
    sg_opts = [
        "set_option projectwdir .",
        f"set_option active_methodology $SPYGLASS_HOME/{self.tool_options['methodology']}",
        "set_option enable_pass_exit_codes yes"
    ]

    # Enable SystemVerilog if needed
    if any(f.get("file_type") == "systemVerilogSource" for f in self.files):
        sg_opts.append("set_option enableSV yes")

    sg_opts.extend([f"set_option {opt}" for opt in self.tool_options["spyglass_options"]])
    self.sg_opts = "\n".join(sg_opts) + "\n\n"

    # Set toplevel
    self.top = f"set_option top {self.toplevel}\n\n"

    # Rule parameters
    self.rule_params = "\n".join(f"set_parameter {r_param}" for r_param in self.tool_options["rule_parameters"]) + "\n\n"

    # Goal options
    self.goal_opts = "\n".join(f"set_goal_option {g_opt}" for g_opt in self.tool_options["goal_options"]) + "\n\n"

    # Source files and include directories
    src_files, incdirs = [], []
    
    for f in self.files:
        if not self._add_include_dir(f, incdirs):
            src_files.append(self.src_file_filter(f))

    self.src_files = "\n".join(src_files) + "\n\n"
    self.incdirs = "\n".join(f"set_option incdir {inc}" for inc in incdirs) + "\n\n" if incdirs else ""

    # Extract and format vlogparam
    if self.vlogparam:
        vlogparams = ["set_option param {"]
        vlogparams.extend(f"  {self.toplevel}.{k}={jinja_filter_param_value_str(v)}" for k, v in self.vlogparam.items())
        vlogparams.append("}\n")
        self.vlogparams = "\n".join(vlogparams)
    else:
        self.vlogparams = ""

    # Extract and format vlogdefine
    if self.vlogdefine:
        vlogdefines = ["set_option define {"]
        vlogdefines.extend(f"  {k}={jinja_filter_param_value_str(v)}" for k, v in self.vlogdefine.items())
        vlogdefines.append("}\n")
        self.vlogdefines = "\n".join(vlogdefines)
    else:
        self.vlogdefines = ""

    # Store full project file content
    self.project_file_content = "\n".join([
        self.sg_opts, self.top, self.rule_params,
        self.goal_opts, self.src_files,
        self.incdirs, self.vlogparams, self.vlogdefines
    ])


        # Template variables for project and scripts
        # self.template_vars = {
        #     "name": self.name,
        #     "methodology": self.tool_options["methodology"],
        #     "goals" : self.tool_options["goals"],
        #     "sanitized_goals" : [],
        #     "goal_options": self.tool_options["goal_options"],
        #     "spyglass_options": sg_opts,
        #     "rule_parameters": self.tool_options["rule_parameters"],
        #     "src_files": src_files,
        #     "filtered_src_files": filtered_src_files,
        #     "incdirs": incdirs,
        #     "has_systemVerilog" : has_systemVerilog,
        #     "toplevel": self.toplevel
        # }
        
        # self.render_template(
        #     "spyglass-project.prj.j2", self.name + ".prj", self.template_vars
        # )

        # # Create a single TCL file for each goal
        # goals = self.tool_options["goals"]
        # sanitized_goals = []

        # for goal in goals:
        #     sanitized_goal = re.sub(r"[^a-zA-Z0-9]", "_", goal).lower()
        #     sanitized_goals.append(sanitized_goal)
            
        #     # Template variables for the current goal
        #     goal_vars = self.template_vars.copy()
        #     goal_vars.update({
        #         "goal": goal,
        #         "sanitized_goal": sanitized_goal,
        #     })

        #     self.render_template(
        #         "spyglass-run-goal.tcl.j2",
        #         f"spyglass-run-{sanitized_goal}.tcl",
        #         goal_vars,
        #     )

        # self.template_vars["sanitized_goals"] = sanitized_goals


        # self.render_template("Makefile.j2", "Makefile", self.template_vars)
        
        self.commands = EdaCommands()
        self.commands.add(
            ["make"],  # Run the Makefile
            ["spyglass","-project", "project_file.prj"],
            ["project_file.prj"],  # List of input source files
        )
        self.commands.set_default_target(" ")
# ----------------------#

    def write_config_files(self):
        s = self.sg_opts + self.top + self.rule_params +  self.goal_opts + self.src_files + self.vlogparams + vlogdefines
        self.update_config_file("spyglass.prj", s)
#.-----------------#

    def src_file_filter(self, f):
        def _vhdl_source(f):
            s = "read_file -type vhdl"
            logical_name = f.get("logical_name")
            if logical_name:
                s += " -library " + logical_name
            return s

        file_types = {
            "verilogSource": "read_file -type verilog",
            "systemVerilogSource": "read_file -type verilog",
            "vhdlSource": _vhdl_source(f),
            "tclSource": "source",
            "waiver": "read_file -type waiver",
            "awl": "read_file -type awl",
            "sgdc": "read_file -type sgdc",
        }
        _file_type = f.get("file_type")  # Access the file_type directly
        if _file_type in file_types:
            return file_types[_file_type] + " " + f["name"]
        elif _file_type == "user":
            return ""  # Ignore user-defined files
        else:
            _s = "{} has unknown file type '{}'"
            logger.warning(_s.format(f["name"], _file_type))
        return ""
