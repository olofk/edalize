from collections import OrderedDict
import os.path
import shutil

import pytest

from edalize import get_edatool


tests_dir = os.path.dirname(__file__)


class TestFixture:
    '''A fixture that makes an edalize backend with work_root directory

    Create this object using the make_edalize_test factory fixture. This passes
    through its `tool_name` and sets up a temporary directory for `work_root`,
    then passes its keyword arguments through to the TestFixture initializer.

    Args:

        tool_name: The name of the tool

        work_root: The directory to treat as a work root

        test_name: The name to call the backend. Defaults to
                   `'test_<tool_name>_0'`

        param_types: A list of parameter types. Defaults to `['plusarg',
                    'vlogdefine', 'vlogparam']` (the parameter types supported
                    by most simulators).

        files: A list of files to use. Defaults to `None`, which means to use
               :py:data:`FILES`.

        tool_options: Dictionary passed to _setup_backend. Defaults to `{}`.

        ref_dir: A reference directory relative to `test_<tool_name>`. Defaults
                 to `'.'`

        use_vpi: If true, set up backend with definitions from :attr:`VPI`.
                 Defaults to `False`.

    '''
    def __init__(self,
                 tool_name,
                 work_root,
                 test_name=None,
                 param_types=['plusarg', 'vlogdefine', 'vlogparam'],
                 files=None,
                 tool_options={},
                 ref_dir='.',
                 use_vpi=False):

        raw_ref_dir = os.path.join(tests_dir, 'test_' + tool_name, ref_dir)

        self.test_name = ('test_{}_0'.format(tool_name)
                          if test_name is None else test_name)
        self.ref_dir = os.path.normpath(raw_ref_dir)
        self.work_root = work_root
        self.backend = _setup_backend(self.test_name, tool_name, param_types,
                                      files, tool_options, work_root, use_vpi)

    def compare_files(self, files, ref_subdir='.'):
        '''Check some files in the work root match those in the ref directory

        The files argument gives the list of files to check. These are
        interpreted as paths relative to the work directory and relative to
        self.ref_dir / ref_subdir.

        This is a wrapper around edalize_common.compare_files: see its
        documentation for how to use the :envvar:`GOLDEN_RUN` environment
        variable to copy across a golden reference.

        '''
        ref_dir = os.path.normpath(os.path.join(self.ref_dir, ref_subdir))
        return compare_files(ref_dir, self.work_root, files)

    def copy_to_work_root(self, path):
        shutil.copy(os.path.join(self.ref_dir, path),
                    os.path.join(self.work_root, path))


@pytest.fixture
def make_edalize_test(monkeypatch, tmpdir):
    '''A factory fixture to make an edalize backend with work_root directory

    The returned factory method takes a `tool_name` (the name of the tool) and
    the keyword arguments supported by :class:`TestFixture`. It returns a
    :class:`TestFixture` object, whose `work_root` is a temporary directory.

    '''
    # Prepend directory `mock_commands` to PATH environment variable
    monkeypatch.setenv('PATH', os.path.join(tests_dir, 'mock_commands'), ':')

    created = []

    def _fun(tool_name, **kwargs):
        work_root = tmpdir / str(len(created))
        work_root.mkdir()
        fixture = TestFixture(tool_name, str(work_root), **kwargs)
        created.append(fixture)
        return fixture

    return _fun


def compare_files(ref_dir, work_root, files):
    """Check that all *files* in *work_root* match those in *ref_dir*.

    If the environment variable :envvar:`GOLDEN_RUN` is set, the *files* in
    *work_root* are copied to *ref_dir* to become the new reference.

    """
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


def _setup_backend(name, tool, paramtypes, files,
                   tool_options, work_root, use_vpi):
    """Set up a backend.

    The backend is called *name*, is set up for *tool* with *tool_options*,
    *paramtypes*, and, if *use_vpi* is ``True``, definitions from :attr:`VPI`.
    If *files* is None, files are taken from :attr:`FILES`.
    """
    parameters = param_gen(paramtypes)

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
            'files'        : FILES if files is None else files,
            'parameters'   : parameters,
            'tool_options' : {tool : tool_options},
            'toplevel'     : 'top_module',
            'vpi'          :  _vpi}

    return get_edatool(tool)(edam=edam, work_root=work_root)


FILES = [
    {"name": "qip_file.qip", "file_type": "QIP"},
    {"name": "qsys_file", "file_type": "QSYS"},
    {"name": "sdc_file", "file_type": "SDC"},
    {"name": "bmm_file", "file_type": "BMM"},
    {"name": "sv_file.sv", "file_type": "systemVerilogSource"},
    {"name": "pcf_file.pcf", "file_type": "PCF"},
    {"name": "ucf_file.ucf", "file_type": "UCF"},
    {"name": "user_file", "file_type": "user"},
    {"name": "tcl_file.tcl", "file_type": "tclSource"},
    {"name": "waiver_file.waiver", "file_type": "waiver"},
    {"name": "vlog_file.v", "file_type": "verilogSource"},
    {"name": "vlog05_file.v", "file_type": "verilogSource-2005"},
    {"name": "vlog_incfile", "file_type": "verilogSource", "is_include_file": True},
    {"name": "vhdl_file.vhd", "file_type": "vhdlSource"},
    {"name": "vhdl_lfile", "file_type": "vhdlSource", "logical_name": "libx"},
    {"name": "vhdl2008_file", "file_type": "vhdlSource-2008"},
    {"name": "xci_file.xci", "file_type": "xci"},
    {"name": "xdc_file.xdc", "file_type": "xdc"},
    {"name": "bootrom.mem", "file_type": "mem"},
    {"name": "c_file.c", "file_type": "cSource"},
    {"name": "cpp_file.cpp", "file_type": "cppSource"},
    {"name": "c_header.h", "file_type": "cSource", "is_include_file": True},
    {"name": "c_header.h", "file_type": "cppSource", "is_include_file": True},
    {"name": "config.vbl", "file_type": "veribleLintRules"},
    {"name": "verible_waiver.vbw", "file_type": "veribleLintWaiver"},
    {"name": "verible_waiver2.vbw", "file_type": "veribleLintWaiver"},
    {'name': 'config.sby.j2', 'file_type': 'sbyConfigTemplate'},
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
