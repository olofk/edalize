from .edalize_common import make_edalize_test


def test_slang_lint(make_edalize_test):
    tool_options = {"mode": "lint"}
    tf = make_edalize_test(
        "slang",
        test_name="test_slang_lint",
        param_types=["vlogdefine", "vlogparam"],
        tool_options=tool_options,
        ref_dir="lint",
    )

    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(["slang.cmd"])


def test_slang_preprocess(make_edalize_test):
    tool_options = {"mode": "preprocess"}
    tf = make_edalize_test(
        "slang",
        test_name="test_slang_preprocess",
        tool_options=tool_options,
        param_types=["vlogdefine", "vlogparam"],
        ref_dir="preprocess",
    )
    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(["slang.cmd"])


def test_slang_slang_options(make_edalize_test):
    tool_options = {"slang_options": ["-v", "-d -c -e"]}
    tf = make_edalize_test(
        "slang",
        test_name="test_slang_slang_options",
        tool_options=tool_options,
        param_types=["vlogdefine", "vlogparam"],
        ref_dir="slang_options",
    )
    tf.backend.configure()
    tf.backend.build()
    tf.backend.run()
    tf.compare_files(["slang.cmd"])
