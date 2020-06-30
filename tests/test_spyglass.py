from edalize_common import make_edalize_test, tests_dir


def run_spyglass_test(tf):
    tf.backend.configure()

    tf.compare_files(['Makefile',
                      'spyglass-run-design_read.tcl',
                      'spyglass-run-lint_lint_rtl.tcl',
                      tf.test_name + '.prj'])

    tf.backend.build()
    tf.compare_files(['spyglass.cmd'])


def test_spyglass_defaults(make_edalize_test):
    """ Test if the SpyGlass backend picks up the tool defaults """
    tf = make_edalize_test('spyglass',
                           param_types=['vlogdefine', 'vlogparam'],
                           ref_dir='defaults')
    run_spyglass_test(tf)


def test_spyglass_tooloptions(make_edalize_test):
    """ Test passing tool options to the Spyglass backend """
    tool_options = {
        'methodology': 'GuideWare/latest/block/rtl_somethingelse',
        'goals': ['lint/lint_rtl', 'some/othergoal'],
        'spyglass_options': ['handlememory yes'],
        'rule_parameters': ['handle_static_caselabels yes'],
    }
    tf = make_edalize_test('spyglass',
                           param_types=['vlogdefine', 'vlogparam'],
                           ref_dir='tooloptions',
                           tool_options=tool_options)
    run_spyglass_test(tf)
