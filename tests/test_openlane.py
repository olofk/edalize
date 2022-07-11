from .edalize_common import make_edalize_test
import os


def test_openlane(make_edalize_test):
    tool_options = {}
    paramtypes = ["vlogdefine"]

    tf = make_edalize_test(
        "openlane", tool_options=tool_options, param_types=paramtypes
    )

    tf.backend.configure()
    tf.backend.build()
    tf.compare_files(["config.tcl", "Makefile", "flow.tcl.cmd"])
