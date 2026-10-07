# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
from pathlib import Path
from xml.etree import ElementTree as ET

from edalize.flows.generic import Generic


class Sim(Generic):
    """Run a simulation"""

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {
        **Generic.FLOW_OPTIONS,
        **{
            "cocotb_module": {
                "type": "str",
                "desc": "Cocotb test python module. (Enables Cocotb simulations)",
            },
        },
    }

    def configure_tools(self, flow):
        if self.flow_options.get("cocotb_module"):
            tool = self.flow_options.get("tool")
            libnamepath = ""
            if tool in ["xcelium"]:
                _, output, _ = self._run_tool(
                    "cocotb-config", ["--lib-name-path", "vpi", tool], quiet=True
                )
                libnamepath = output.decode("utf8").strip()

            cocotb_options = {
                "ghdl": (
                    "sim_options",
                    ["--vpi=`cocotb-config --lib-name-path vpi ghdl`"],
                ),
                "icarus": (
                    "vvp_options",
                    [
                        "-M",
                        "`cocotb-config --lib-dir`",
                        "-m",
                        "`cocotb-config --lib-name vpi icarus`",
                    ],
                ),
                "modelsim": (
                    "vsim_options",
                    ["-pli", "`cocotb-config --lib-name-path vpi questa`"],
                ),
                "vcs": (
                    "vcs_options",
                    [
                        "-debug",
                        "+vpi",
                        "-P",
                        "pli.tab",
                        "-load",
                        "$(cocotb-config --lib-name-path vpi vcs)",
                    ],
                ),
                "verilator": (
                    "verilator_options",
                    [
                        "--vpi",
                        "--public-flat-rw --prefix Vtop",
                        '-LDFLAGS "-Wl,-rpath,`cocotb-config --lib-dir` -L`cocotb-config --lib-dir` -lcocotbvpi_verilator"',
                    ],
                ),
                "xcelium": (
                    # Note: xrun may throw a 'No such file or directory' error
                    # about libpython3.x.so while loading the VPI library if
                    # the user using a virtualenv or conda environment.
                    # User can fix this by adding the python library path to
                    # LD_LIBRARY_PATH environment variable before launching xrun.
                    "xrun_options",
                    [
                        "-access +rwc",
                        f"-loadvpi {libnamepath}:vlog_startup_routines_bootstrap",
                    ],
                ),
            }
            (opt, val) = cocotb_options[tool]
            self.edam["tool_options"][tool][opt] = (
                self.edam["tool_options"][tool].get(opt, []) + val
            )

        super().configure_tools(flow)

    def configure(self):
        if self.flow_options.get("tool") == "vcs":
            with open(os.path.join(self.work_root, "pli.tab"), "w") as f:
                f.write("acc+=rw,wn:*\n")
        super().configure()

    def _has_vhdl(self):
        return any(
            f.get("file_type", "").startswith("vhdlSource")
            for f in self.edam.get("files", [])
        )

    def run(self, args=None):
        tool = self.flow_options.get("tool")
        run_tool = self.flow.get_node(tool).inst

        # Get run command from simulator
        (cmd, args, cwd) = run_tool.run()

        cocotb_module = self.flow_options.get("cocotb_module")
        if cocotb_module:
            # Get required cocotb env data
            prev_verbose = self.verbose
            self.verbose = False
            _, libpy, _ = self._run_tool("cocotb-config", ["--libpython"], quiet=True)
            _, pybin, _ = self._run_tool("cocotb-config", ["--python-bin"], quiet=True)

            env = {
                "COCOTB_TEST_MODULES": cocotb_module,
                "MODULE": cocotb_module,  # Keep for compatibility with cocotb < v2.0
                "LIBPYTHON_LOC": libpy.decode("utf-8").strip(),
                "PYGPI_PYTHON_BIN": pybin.decode("utf-8").strip(),
            }

            # A VHDL design is driven through VHPI, which is loaded next to the
            # VPI library that configure_tools already put on the command line.
            # https://docs.cocotb.org/en/stable/custom_flows.html
            if tool == "xcelium" and self._has_vhdl():
                _, vhpi, _ = self._run_tool(
                    "cocotb-config", ["--lib-name-path", "vhpi", tool], quiet=True
                )
                env["GPI_EXTRA"] = (
                    vhpi.decode("utf-8").strip() + ":cocotbvhpi_entry_point"
                )
                args += ["-NEW_VHPI_PROPAGATE_DELAY"]

            self.verbose = prev_verbose
        else:
            env = {}

        self._run_tool(cmd, args=args, cwd=cwd, env=env)

        if cocotb_module:
            # Check for failed tests from generated JUnit XML file. Support for cocotb 1.9 and 2.0
            results_xml = Path(cwd) / "results.xml"

            if not results_xml.exists():
                # Cocotb 2.0 with pytest as runner
                pytest_current_test: str | None = os.environ.get("PYTEST_CURRENT_TEST")

                if pytest_current_test:
                    # https://github.com/cocotb/cocotb/blob/v2.0.1/src/cocotb_tools/runner.py#L516
                    current_test_name: str = pytest_current_test.split(":")[-1].split(
                        " "
                    )[0]
                    results_xml = Path(cwd) / f"{current_test_name}.result.xml"

            self._check_junit_xml(results_xml)

    def _check_junit_xml(self, file: Path) -> None:
        """Check test results from generated JUnit XML file.

        Args:
            file: Path to generated JUnit XML file with test results.

        Raises:
            FileExistsError: When JUnit XML file was not found.
            RuntimeError: When one of tests failed.
        """
        if not file.exists():
            raise FileExistsError(
                f"ERROR: Simulation terminated abnormally. Results file {file} not found."
            )

        failed: int = 0
        tests: int = 0

        for testsuite in ET.parse(file).getroot().findall("testsuite"):
            for testcase in testsuite.findall("testcase"):
                failed += len(testcase.findall("failure"))
                failed += len(testcase.findall("error"))
                tests += 1

        if failed:
            raise RuntimeError(f"ERROR: Failed {failed} of {tests} tests.")
