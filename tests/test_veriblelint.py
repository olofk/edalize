from edalize_common import make_edalize_test


def test_veriblelint_default(make_edalize_test):
    """ Test the lint mode of Verible """
    tf = make_edalize_test('veriblelint',
                           test_name='test_verible',
                           param_types=['vlogdefine', 'vlogparam'],
                           ref_dir='lint')
    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(['verible-verilog-lint.cmd'])
