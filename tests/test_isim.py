from edalize_common import make_edalize_test


def test_isim(make_edalize_test):
    tool_options = {
        'fuse_options': ['some', 'fuse_options'],
        'isim_options': ['a', 'few', 'isim_options'],
    }
    tf = make_edalize_test('isim',
                           tool_options=tool_options)

    tf.backend.configure()

    tf.compare_files(['config.mk',
                      'Makefile',
                      'run_test_isim_0.tcl',
                      'test_isim_0.prj'])

    tf.copy_to_work_root('test_isim_0')

    tf.backend.run()

    tf.compare_files(['run.cmd'])
