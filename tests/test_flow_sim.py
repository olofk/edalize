import filecmp
import os
from .edalize_flow_common import flow_fixture
from .edalize_common import tests_dir


def test_flow_sim_modelsim(flow_fixture):
    flow_options = {
        "tool": "modelsim",
    }

    ff = flow_fixture("sim", flow_options=flow_options, ref_subdir="modelsim")

    ff.compare_makefile()
    ff.compare_config_files(
        ["edalize_build_rtl.tcl", "edalize_main.tcl", "modelsim-makefile"]
    )
