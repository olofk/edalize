import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "edalize",
    version = "0.1.2",
    packages=['edalize'],
    package_data = {'edalize' : [
        'templates/icestorm/icestorm-makefile.j2',
        'templates/spyglass/Makefile.j2',
        'templates/spyglass/spyglass-project.prj.j2',
        'templates/spyglass/spyglass-run-goal.tcl.j2',
        'templates/vcs/Makefile.j2',
        'templates/vivado/vivado-makefile.j2',
        'templates/vivado/vivado-program.tcl.j2',
        'templates/vivado/vivado-project.tcl.j2',
        'templates/vivado/vivado-run.tcl.j2',
        'templates/quartus/quartus-project.tcl.j2',
        'templates/quartus/quartus-std-makefile.j2',
        'templates/quartus/quartus-pro-makefile.j2',
        'templates/trellis/trellis-makefile.j2'
    ]},
    author = "Olof Kindgren",
    author_email = "olof.kindgren@gmail.com",
    description = ("Edalize is a library for interfacing EDA tools, primarily for FPGA development"),
    license = "",
    keywords = ["VHDL", "verilog", "EDA", "hdl", "rtl", "synthesis", "FPGA", "simulation", "Xilinx", "Altera"],
    url = "https://github.com/olofk/edalize",
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "Topic :: Utilities",
    ],
    install_requires=[
        'pytest>=3.3.0',
        'Jinja2>=2.8',
    ],
    tests_require=[
        'pyyaml',
    ],
)
