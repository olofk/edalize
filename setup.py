# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="edalize",
    use_scm_version={
        "relative_to": __file__,
        "write_to": "edalize/version.py",
    },
    packages=["edalize", "edalize.tools", "edalize.flows"],
    package_data={
        "edalize": [
            "templates/yosys/edalize_yosys_procs.tcl.j2",
            "templates/yosys/yosys-script-tcl.j2",
            "templates/openfpga/task_simulation.conf.j2",
            "templates/spyglass/Makefile.j2",
            "templates/spyglass/spyglass-project.prj.j2",
            "templates/spyglass/spyglass-run-goal.tcl.j2",
            "templates/vcs/Makefile.j2",
            "templates/vivado/vivado-program.tcl.j2",
            "templates/vivado/vivado-project.tcl.j2",
            "templates/vivado/vivado-run.tcl.j2",
            "templates/vivado/vivado-synth.tcl.j2",
            "templates/vunit/run.py.j2",
            "templates/quartus/quartus-project.tcl.j2",
            "templates/quartus/quartus-std-makefile.j2",
            "templates/quartus/quartus-pro-makefile.j2",
            "templates/ascentlint/Makefile.j2",
            "templates/ascentlint/run-ascentlint.tcl.j2",
            "templates/libero/libero-project.tcl.j2",
            "templates/libero/libero-run.tcl.j2",
            "templates/libero/libero-syn-user.tcl.j2",
            "templates/ghdl/Makefile.j2",
            "templates/openlane/openlane-makefile.j2",
            "templates/openlane/openlane-script-tcl.j2",
            "templates/design_compiler/design-compiler-makefile.j2",
            "templates/design_compiler/design-compiler-project.tcl.j2",
            "templates/design_compiler/design-compiler-read-sources.tcl.j2",
            "templates/genus/genus-makefile.j2",
            "templates/genus/genus-project.tcl.j2",
            "templates/genus/genus-read-sources.tcl.j2",
        ],
        "edalize.tools": [
            "templates/efinity/isf_to_xml.py",
            "templates/efinity/newproj_tmpl.xml.j2",
            "templates/yosys/edalize_yosys_procs.tcl.j2",
            "templates/yosys/yosys-script-tcl.j2",
            "templates/vivado/vivado-netlist.tcl.j2",
            "templates/vivado/vivado-program.tcl.j2",
            "templates/vivado/vivado-project.tcl.j2",
            "templates/vivado/vivado-run.tcl.j2",
            "templates/vivado/vivado-synth.tcl.j2",
        ],
    },
    author="Olof Kindgren",
    author_email="olof.kindgren@gmail.com",
    description=(
        "Library for interfacing EDA tools such as simulators, linters or synthesis tools, using a common interface"
    ),
    license="BSD-2-Clause",
    keywords=[
        "VHDL",
        "verilog",
        "EDA",
        "hdl",
        "rtl",
        "synthesis",
        "FPGA",
        "simulation",
        "Xilinx",
        "Altera",
    ],
    url="https://github.com/olofk/edalize",
    long_description=read("README.rst"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Utilities",
    ],
    setup_requires=[
        "setuptools_scm < 7.0; python_version<'3.7'",
        "setuptools_scm; python_version>='3.7'",
    ],
    install_requires=[
        "Jinja2>=3",
    ],
    tests_require=["pytest>=3.3.0", "vunit_hdl>=4.0.8"],
    # The reporting modules have dependencies that shouldn't be required for
    # all Edalize users.
    extras_require={
        "reporting": ["pyparsing<3.1.0", "pandas"],
    },
    # Supported Python versions: 3.6+
    python_requires=">=3.6, <4",
    scripts=["scripts/el_docker"],
)
