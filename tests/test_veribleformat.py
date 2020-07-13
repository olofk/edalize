from edalize_common import make_edalize_test


def test_veribleformat_default(make_edalize_test):
    """ Test the format mode of Verible """
    tf = make_edalize_test('veribleformat',
                           test_name='test_verible',
                           param_types=['vlogdefine', 'vlogparam'],
                           ref_dir='default')
    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(['verible-verilog-format.cmd'])
