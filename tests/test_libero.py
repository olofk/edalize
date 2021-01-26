from edalize_common import make_edalize_test

def test_libero(make_edalize_test):
    """ Test passing tool options to the Libero backend """
    name = 'libero-project'
    tool_options = {
        'family'          : 'Polarfire',
        'die'             : 'MPF300TS_ES',
        'package'         : 'FCG1152'
    }

    tf = make_edalize_test('libero',
                           test_name=name,
                           tool_options=tool_options)

    tf.backend.configure()
    tf.compare_files([name + '.tcl'])
