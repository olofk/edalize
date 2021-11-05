# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="edalize",
    version="0.2.5",
    packages=["edalize"],
    package_data={
        "edalize": [
            "templates/yosys/edalize_yosys_procs.tcl.j2",
            "templates/yosys/yosys-script-tcl.j2",
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
        ]
    },
    author="Olof Kindgren",
    author_email="olof.kindgren@gmail.com",
    description=(
        "Edalize is a library for interfacing EDA tools, primarily for FPGA development"
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
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Utilities",
    ],
    install_requires=[
        # 2.11.0 and .1 introduced an incompatible change in template output,
        # which was fixed in 2.11.2 and later.
        # https://github.com/pallets/jinja/issues/1138
        "Jinja2>=2.11.3",
    ],
    tests_require=["pytest>=3.3.0", "vunit_hdl>=4.0.8"],
    # The reporting modules have dependencies that shouldn't be required for
    # all Edalize users.
    extras_require={
        "reporting": ["pyparsing", "pandas"],
    },
    # Supported Python versions: 3.6+
    python_requires=">=3.6, <4",
)
