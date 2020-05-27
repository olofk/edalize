from os.path import dirname
from pathlib import Path

import cocotb


'''
Knowledge of the library and any associated options could be held by cocotb,
perhaps obtained via cocotb-config
'''


def get_ghdl_args(toplevel_lang):
    if toplevel_lang != 'vhdl':
        raise RuntimeError('GHDL only supports VHDL')

    ghdl_cocotb_lib = Path(dirname(cocotb.__file__)) / 'libs' / 'libcocotbvpi_ghdl.so'
    args = f"--vpi={ghdl_cocotb_lib}"

    return args


def get_icarus_args(toplevel_lang):
    if toplevel_lang != 'verilog':
        raise RuntimeError('Icarus only supports Verilog')

    cocotb_lib_dir = Path(dirname(cocotb.__file__)) / 'libs'
    args = f"-M {cocotb_lib_dir} -m libcocotbvpi_icarus"

    return args


'''
Knowledge of where to add the options belongs with edalize. This is required
because the simulator backends are not consistent in their requirements at the
moment.
'''


def get_ghdl_option_name():
    return 'run_options'


def get_icarus_option_name():
    return 'vpp_options'


'''
Finally provide access to the options.
'''

simulator_args = {
    'ghdl': (get_ghdl_option_name, get_ghdl_args),
    'icarus': (get_icarus_option_name, get_icarus_args)
}


def get_cocotb_args(simulator, toplevel_lang):
    if simulator not in simulator_args:
        raise RuntimeError('Simulator not supported in cocotb backend')

    (option_name, args) = simulator_args[simulator]

    return option_name(), args(toplevel_lang)
