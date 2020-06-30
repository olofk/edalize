import os
import pytest
from edalize_common import make_edalize_test


def run_icestorm_test(tf, pnr_cmdfile='arachne-pnr.cmd'):
    tf.backend.configure()

    tf.compare_files(['Makefile', tf.test_name + '.tcl'])

    f = os.path.join(tf.work_root, 'pcf_file.pcf')
    with open(f, 'a'):
        os.utime(f, None)

    tf.backend.build()
    tf.compare_files(['yosys.cmd', pnr_cmdfile, 'icepack.cmd'])


def test_icestorm(make_edalize_test):
    tool_options = {
        'yosys_synth_options': ['some', 'yosys_synth_options'],
        'arachne_pnr_options': ['a', 'few', 'arachne_pnr_options']
    }
    tf = make_edalize_test('icestorm',
                           param_types=['vlogdefine', 'vlogparam'],
                           tool_options=tool_options)

    run_icestorm_test(tf)


def test_icestorm_minimal(make_edalize_test):
    files = [{'name': 'pcf_file.pcf', 'file_type': 'PCF'}]
    tf = make_edalize_test('icestorm',
                           param_types=[],
                           files=files,
                           ref_dir='minimal')

    run_icestorm_test(tf)


def test_icestorm_no_pcf(make_edalize_test):
    tf = make_edalize_test('icestorm',
                           param_types=[],
                           files=[])

    tf.backend.configure()
    assert os.path.exists(os.path.join(tf.work_root, 'empty.pcf'))


def test_icestorm_multiple_pcf(make_edalize_test):
    files = [{'name': 'pcf_file.pcf', 'file_type': 'PCF'},
             {'name': 'pcf_file2.pcf', 'file_type': 'PCF'}]
    tf = make_edalize_test('icestorm',
                           param_types=[],
                           files=files)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Icestorm backend supports only one PCF file. Found pcf_file.pcf, pcf_file2.pcf" in str(e.value)


def test_icestorm_nextpnr(make_edalize_test):
    tool_options = {
        'yosys_synth_options': ['some', 'yosys_synth_options'],
        'arachne_pnr_options': ['a', 'few', 'arachne_pnr_options'],
        'nextpnr_options': ['multiple', 'nextpnr_options'],
        'pnr': 'next'
    }
    tf = make_edalize_test('icestorm',
                           param_types=['vlogdefine', 'vlogparam'],
                           tool_options=tool_options,
                           ref_dir='nextpnr')

    run_icestorm_test(tf, pnr_cmdfile='nextpnr-ice40.cmd')


def test_icestorm_invalid_pnr(make_edalize_test):
    name = 'test_icestorm_0'
    tf = make_edalize_test('icestorm',
                           test_name=name,
                           param_types=['vlogdefine', 'vlogparam'],
                           tool_options={'pnr': 'invalid'},
                           ref_dir='nextpnr')

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "nvalid pnr option 'invalid'. Valid values are 'arachne' for Arachne-pnr or 'next' for nextpnr" in str(e.value)
