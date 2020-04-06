import os.path
import tempfile
from collections import OrderedDict

from edalize import get_edatool

tests_dir = os.path.dirname(__file__)

def compare_files(ref_dir, work_root, files):
    """Check that all *files* in *work_root* match those in *ref_dir*.

    If the environment variable :envvar:`GOLDEN_RUN` is set,
    the *files* in *work_root* are copied to *ref_dir* to become the new reference.
    """

    import os.path
    import shutil

    for f in files:
        reference_file = os.path.join(ref_dir, f)
        generated_file = os.path.join(work_root, f)

        assert os.path.exists(generated_file)

        if 'GOLDEN_RUN' in os.environ:
            shutil.copy(generated_file, reference_file)

        with open(reference_file) as fref, open(generated_file) as fgen:
            assert fref.read() == fgen.read(), f


def param_gen(paramtypes):
    """Generate dictionary of definitions in *paramtypes* list."""

    defs = OrderedDict()
    for paramtype in paramtypes:
        for datatype in ['bool', 'int', 'str']:
            if datatype == 'int':
                default = 42
            elif datatype == 'str':
                default = 'hello'
            else:
                default = True
            defs[paramtype+'_'+datatype] = {
                'datatype'    : datatype,
                'default'     : default,
                'description' : '',
                'paramtype'   : paramtype}
    return defs


def setup_backend_minimal(name, tool, files):
    """Set up a minimal backend.

    The backend is called *name*, is set up for *tool* and uses *files*.
    """

    # prepend directory `mock_commands` to PATH environment variable
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']

    work_root = tempfile.mkdtemp(prefix=tool+'_')

    edam = {'name'         : name,
            'files'        : files,
            'toplevel'     : 'top_module',
    }
    return (get_edatool(tool)(edam=edam,
                              work_root=work_root), work_root)


def setup_backend(paramtypes, name, tool, tool_options, use_vpi=False):
    """Set up a backend.

    The backend is called *name*, is set up for *tool* with *tool_options*,
    *paramtypes*, and, if *use_vpi* is ``True``, definitions from :attr:`VPI`.
    Files are taken from :attr:`FILES`.
    """

    # prepend directory `mock_commands` to PATH environment variable
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    parameters = param_gen(paramtypes)

    work_root = tempfile.mkdtemp(prefix=tool+'_')

    _vpi = []
    if use_vpi:
        _vpi = VPI
        for v in VPI:
            for f in v['src_files']:
                _f = os.path.join(work_root, f)
                if not os.path.exists(os.path.dirname(_f)):
                    os.makedirs(os.path.dirname(_f))
                with open(_f, 'a'):
                    os.utime(_f, None)

    edam = {'name'         : name,
            'files'        : FILES,
            'parameters'   : parameters,
            'tool_options' : {tool : tool_options},
            'toplevel'     : 'top_module',
            'vpi'          :  _vpi}

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    return (backend, work_root)


FILES = [
    {'name' : 'qip_file.qip' , 'file_type' : 'QIP'},
    {'name' : 'qsys_file'    , 'file_type' : 'QSYS'},
    {'name' : 'sdc_file'     , 'file_type' : 'SDC'},
    {'name' : 'bmm_file'     , 'file_type' : 'BMM'},
    {'name' : 'sv_file.sv'   , 'file_type' : 'systemVerilogSource'},
    {'name' : 'pcf_file.pcf' , 'file_type' : 'PCF'},
    {'name' : 'ucf_file.ucf' , 'file_type' : 'UCF'},
    {'name' : 'user_file'    , 'file_type' : 'user'},
    {'name' : 'tcl_file.tcl' , 'file_type' : 'tclSource'},
    {'name' : 'vlog_file.v'  , 'file_type' : 'verilogSource'},
    {'name' : 'vlog05_file.v', 'file_type' : 'verilogSource-2005'},
    {'name' : 'vlog_incfile' , 'file_type' : 'verilogSource', 'is_include_file' : True},
    {'name' : 'vhdl_file.vhd', 'file_type' : 'vhdlSource'},
    {'name' : 'vhdl_lfile'   , 'file_type' : 'vhdlSource', 'logical_name' : 'libx'},
    {'name' : 'vhdl2008_file', 'file_type' : 'vhdlSource-2008'},
    {'name' : 'xci_file.xci' , 'file_type' : 'xci'},
    {'name' : 'xdc_file.xdc' , 'file_type' : 'xdc'},
    {'name' : 'bootrom.mem'  , 'file_type' : 'mem'},
    {'name' : 'c_file.c'     , 'file_type' : 'cSource'},
    {'name' : 'cpp_file.cpp' , 'file_type' : 'cppSource'},
    {'name' : 'c_header.h'   , 'file_type' : 'cSource', 'is_include_file' : True},
    {'name' : 'c_header.h'   , 'file_type' : 'cppSource', 'is_include_file' : True},
    {'name' : 'config.vbl'   , 'file_type' : 'veribleLintRules'}
]
"""Files of all supported file types."""


VPI = [
    {'src_files': ['src/vpi_1/f1',
                   'src/vpi_1/f3'],
     'include_dirs': ['src/vpi_1/'],
     'libs': ['some_lib'],
     'name': 'vpi1'},
    {'src_files': ['src/vpi_2/f4'],
     'include_dirs': [],
     'libs': [],
     'name': 'vpi2'}]
"""Predefined VPI modules to build."""
