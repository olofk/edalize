from edalize import *
import os

work_root = 'build'

files = [
    {'name': os.path.relpath('rtl/serv_bufreg.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_alu.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_csr.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_ctrl.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_decode.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_immdec.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_mem_if.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_rf_if.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_rf_ram_if.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_rf_ram.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_state.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_top.v', work_root),
     'file_type': 'verilogSource'},
    {'name': os.path.relpath('rtl/serv_rf_top.v', work_root),
     'file_type': 'verilogSource'}
]

parameters = {}

tool = 'openlane'

edam = {
    'files' : files,
    'name' : 'serv',
    'parameters' : parameters,
    'toplevel' : 'serv_top'
}

backend = get_edatool(tool)(edam=edam, work_root=work_root)

os.makedirs(work_root)
backend.configure()
backend.build()
