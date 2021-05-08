from edalize_common import make_edalize_test

def test_slang_lint(make_edalize_test):
    mode = "lint"
    tool_options = {
        'mode' : mode
    }
    tf = make_edalize_test('slang',
                           param_types=['vlogdefine'],
                           tool_options=tool_options,
                           ref_dir='lint')

    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(['slang.cmd'])

def test_slang_preprocess(make_edalize_test):
    tf = make_edalize_test('slang',
                           test_name="test_slang_preprocess",
                           tool_options={'mode': "preprocess"},
                           param_types=['vlogdefine'],
                           ref_dir="preprocess")
    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(['slang.cmd'])
