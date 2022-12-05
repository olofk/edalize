from .edalize_common import make_edalize_test


def test_libero(make_edalize_test):
    """Test passing tool options to the Libero backend"""
    name = "libero-test"
    tool_options = {"family": "PolarFire", "die": "MPF300TS_ES", "package": "FCG1152"}

    tf = make_edalize_test("libero", test_name=name, tool_options=tool_options)

    tf.backend.configure()
    tf.compare_files(
        [
            name + "-project.tcl",
            name + "-run.tcl",
            name + "-syn-user.tcl",
        ]
    )


def test_libero_with_params(make_edalize_test):
    """Test passing tool options to the Libero backend"""
    name = "libero-test-all"
    tool_options = {
        "family": "PolarFire",
        "die": "MPF300TS_ES",
        "package": "FCG1152",
        "speed": "-1",
        "dievoltage": "1.0",
        "range": "EXT",
        "defiostd": "LVCMOS 1.8V",
        "hdl": "VHDL",
    }

    tf = make_edalize_test("libero", test_name=name, tool_options=tool_options)

    tf.backend.configure()
    tf.compare_files(
        [
            name + "-project.tcl",
            name + "-run.tcl",
            name + "-syn-user.tcl",
        ]
    )
