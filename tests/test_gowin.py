from .edalize_common import make_edalize_test


def test_gowin(make_edalize_test):
    tool_options = {
        "device": "GW2AR-LV18QN88C8/I7",
    }


    _tool_options = {**tool_options}

    tf = make_edalize_test(
        "gowin",
        param_types=["vlogdefine", "vlogparam"],
        tool_options=_tool_options,
    )

    tf.backend.configure()
    tf.compare_files(["Makefile", tf.test_name + ".tcl"])

