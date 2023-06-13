# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import logging
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

"""
OpenFPGA Flow Backend.

A core (usually the system core) can add the following files:

* Benchmark RTL sources (Yosys supports only Verilog file type) and module name
* The target FPGA architecture name, made with OpenFPGA fabric flow (SOFA,...)
* Source the required environment variables: OPENFPGA_PATH, SOFA_PATH
* Optional parameters: task options ('--debug', ...)
"""

SOFA_TASK_DIRS = {
    "sofa-chd": "FPGA1212_SOFA_CHD_PNR/FPGA1212_SOFA_CHD_task",
    "sofa-hd": "FPGA1212_SOFA_HD_PNR/FPGA1212_SOFA_HD_task",
    "sofa-plus-hd": "FPGA1212_SOFA_PLUS_HD_PNR/FPGA1212_SOFA_PLUS_HD_task",
    "sofa-qlhd": "FPGA1212_QLSOFA_HD_PNR/FPGA1212_QLSOFA_HD_task",
}


class Openfpga(Edatool):

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The OpenFPGA backend executes Yosys synthesis tool and VPR place and route. It can target multiple different open-source FPGAs (supported: sofa-chd, sofa-hd, sofa-qlhd, sofa-plus-hd)",
                "members": [
                    {
                        "name": "arch",
                        "type": "String",
                        "desc": "Target architecture. Legal values are *sofa* and *sofa-plus*.",
                    },
                ],
                "lists": [
                    {
                        "name": "task_options",
                        "type": "String",
                        "desc": "Additional options for OpenFPGA task flow execution.",
                    },
                ],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=False):
        """
        This calls the parent constructor, but also identifies whether the
        current system has correctly set the following environment variables:

        - ``OPENFPGA_PATH``: directory of the OpenFPGA framework, available here: https://github.com/lnis-uofu/OpenFPGA

        - ``SOFA_PATH``: directory of the SOFA eFPGA IPs, available here: https://github.com/lnis-uofu/SOFA
        """
        super(Openfpga, self).__init__(edam, work_root, verbose)

        # Check environment variable setup
        if os.environ.get("OPENFPGA_PATH") is None:
            raise RuntimeError(
                """\
Environment variable 'OPENFPGA_PATH' was not found!
Download, build and source the framework: https://github.com/lnis-uofu/OpenFPGA"""
            )
        if os.environ.get("SOFA_PATH") is None:
            raise RuntimeError(
                """\
Environment variable 'SOFA_PATH' was not found!
Download and source the project: https://github.com/lnis-uofu/SOFA"""
            )

        self.openfpga_path = os.environ["OPENFPGA_PATH"]
        self.openfpga_flow = f"{self.openfpga_path}/openfpga_flow"
        self.sofa_path = os.environ["SOFA_PATH"]

    def _write_testbench(self):
        """
        As required by the OpenFPGA configuration format specifications, the
        benchmark variable need to be a Verilog file type, a made up of
        multiple files.
        """
        (src_files, inc_dirs) = self._get_fileset_files(force_slash=True)

        # Create the benchmark variable, as a list of files using absolute path
        tb_files = []
        for f in src_files:
            # check the correct file type
            if not f.file_type.startswith("verilogSource"):
                logger.warning(f"File type not supported for '{f.name}'")
                continue
            # find the absolute path
            if os.path.isfile(f.name):
                fname = f.name
            elif os.path.isfile(f"{self.work_root}/{f.name}"):
                fname = f.name
            else:
                logger.error(f"Can't found file '{f.name}'")
                continue
            tb_files.append(fname)

        if len(tb_files) == 0:
            logger.error("Missing testbench source file(s)!")

        self.testbench_file = ",".join(tb_files)

    def configure_main(self):
        """
        Configuration is the first phase of the build.

        This writes an OpenFPGA task file for SOFA/SOFA+ architectures, which
        will generate the according OpenFPGA flow. It first collects all
        verilog sources, top_module and then writes them into the task file.

        Note: OpenFPGA flow may uses Yosys/VPR backend for Synthesis and P&R,
        respectively.
        """
        # Create a single testbench file
        self._write_testbench()

        # Set the target architecture and its dependencies
        arch = self.tool_options.get("arch")
        if arch is None:
            raise RuntimeError("Missing required option 'arch'")
        if not arch in SOFA_TASK_DIRS:
            raise RuntimeError(f"Unsupported FPGA architecture: 'arch={arch}'")

        # Workspace variables
        sofa_dir = f"{self.sofa_path}/{SOFA_TASK_DIRS[arch]}"
        flow_dir = self.openfpga_flow

        template_vars = {
            "power_tech_file": f"{flow_dir}/tech/PTM_45nm/45nm.xml",
            "openfpga_sim_setting_file": f"{flow_dir}/openfpga_simulation_settings/auto_sim_openfpga.xml",
            "arch_variable_file": f"{sofa_dir}/design_variables.yml",
            "openfpga_shell_template": f"{sofa_dir}/generate_testbench.openfpga",
            "openfpga_arch_file": f"{sofa_dir}/arch/openfpga_arch.xml",
            "external_fabric_key_file": f"{sofa_dir}/arch/fabric_key.xml",
            "vpr_arch_file": f"{sofa_dir}/arch/vpr_arch.xml",
            "tb_verilog_file": self.testbench_file,
            "tb_top_entity": self.toplevel,
        }

        # Specific features by architectures
        if arch == "sofa-chd":
            template_vars.update(
                {
                    "vpr_device_layout": "12x12",
                    "vpr_route_chan_width": "60",
                }
            )
        if arch == "sofa-hd":
            template_vars.update(
                {
                    "vpr_device_layout": "12x12",
                    "vpr_route_chan_width": "40",
                }
            )
        if arch == "sofa-plus-hd":
            template_vars.update(
                {
                    "openfpga_sim_setting_file": f"{flow_dir}/openfpga_simulation_settings/fixed_sim_openfpga.xml",
                    "vpr_device_layout": "12x12",
                    "vpr_route_chan_width": "60",
                }
            )
        if arch == "sofa-qlhd":
            template_vars.update(
                {
                    "vpr_device_layout": "12x12",
                    "vpr_route_chan_width": "60",
                }
            )

        # Render the OpenFPGA task configuration file
        try:
            os.makedirs(os.path.join(self.work_root, "config"))
        except:
            pass
        self.render_template(
            "task_simulation.conf.j2", "config/task.conf", template_vars
        )

    def build_main(self):
        pass

    def run_main(self):
        """
        Run the FPGA simulation.
        """
        # NOTE: edalize subprocess runs the current tool from the work_root
        # directory, where the 'config/' dir is located.
        task_script = f"{self.openfpga_flow}/scripts/run_fpga_task.py"
        task_options = self.tool_options.get("task_options", [])
        args = [task_script, "."] + task_options

        logger.info("run OpenFPGA simulation task")
        self._run_tool("python3", args)
