from edalize_common import make_edalize_test


def test_ascentlint_defaults(make_edalize_test):
    """ Test the default configuration of Ascent Lint """
    tf = make_edalize_test('ascentlint',
                           test_name='test_ascentlint',
                           param_types=['vlogdefine', 'vlogparam'],
                           ref_dir='defaults')

    tf.backend.configure()

    tf.compare_files(['Makefile', 'run-ascentlint.tcl', 'sources.f'])

    tf.backend.build()

    tf.compare_files(['ascentlint.cmd'])
