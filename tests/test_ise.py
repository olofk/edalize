from edalize_common import make_edalize_test
import pytest


def test_ise(make_edalize_test):
    name = 'test_ise_0'
    tool_options = {
        'family': 'spartan6',
        'device': 'xc6slx45',
        'package': 'csg324',
        'speed': '-2'
    }
    tf = make_edalize_test('ise',
                           test_name=name,
                           param_types=['vlogdefine', 'vlogparam'],
                           tool_options=tool_options)

    tf.backend.configure()

    tf.compare_files(['Makefile', 'config.mk',
                      name + '.tcl', name + '_run.tcl'])

    tf.backend.build()
    tf.compare_files(['xtclsh.cmd'])


def test_ise_missing_options(make_edalize_test):
    tool_options = {
        'family': 'spartan6',
        'device': 'xc6slx45',
        'package': 'csg324',
    }
    tf = make_edalize_test('ise',
                           param_types=['vlogdefine', 'vlogparam'],
                           tool_options=tool_options)

    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()
    assert "Missing required option 'speed'" in str(e.value)
