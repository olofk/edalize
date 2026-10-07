from .edalize_common import make_edalize_test


def test_slang_constructor_runs(make_edalize_test):
    # Regression for the ``def __init`` (note the missing trailing ``__``)
    # typo: the constructor never fired, so the instance-level attributes
    # below were never initialised and ``self.verbose`` was not propagated
    # from the Edatool base class. Build the backend through the standard
    # fixture and inspect the resulting instance.
    tf = make_edalize_test(
        "slang",
        test_name="test_slang_constructor_runs",
        tool_options={"mode": "lint"},
        ref_dir="lint",
    )
    backend = tf.backend
    assert backend.rtl_paths is None
    assert backend.incdirs is None
    assert backend.gen_rtl_name is None
    # ``flags`` is per-instance (not the shared class attribute) once the
    # constructor has fired.
    assert backend.flags == []
    assert backend.flags is not type(backend).flags
    # ``verbose`` is forwarded through to Edatool by the constructor.
    assert isinstance(backend.verbose, bool)


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
