from edalize_common import make_edalize_test
import pytest

def test_libero(make_edalize_test):
    """ Test passing tool options to the Libero backend """
    name = 'libero-test'
    tool_options = {
        'family': 'PolarFire',
        'die': 'MPF300TS_ES',
        'package': 'FCG1152'
    }

    tf = make_edalize_test('libero',
                           test_name=name,
                           tool_options=tool_options)

    tf.backend.configure()
    tf.compare_files([name + '-project.tcl', name +
                      '-run.tcl', name + '-syn-user.tcl', ])


@pytest.mark.parametrize("params", [("v12_5", False), ("v2021_1", True)])
def test_libero_with_params(params,make_edalize_test):
    """ Test passing tool options to the Libero backend """

    test_name, v2021_or_later = params

    name = 'libero-test-all-' + test_name
    tool_options = {
        'family': 'PolarFire',
        'die': 'MPF300TS_ES',
        'package': 'FCG1152',
        'speed': '-1',
        'dievoltage': '1.0',
        'range': 'EXT',
        'defiostd': 'LVCMOS 1.8V',
        'hdl': 'VHDL',
    }
    if v2021_or_later:
        tool_options['v2021_or_later'] = 'true'

    tf = make_edalize_test('libero',
                           test_name=name,
                           tool_options=tool_options)

    tf.backend.configure()
    tf.compare_files([name + '-project.tcl', name +
                      '-run.tcl', name + '-syn-user.tcl', ])
