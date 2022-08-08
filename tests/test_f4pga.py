import os
import pytest
from edalize_common import make_edalize_test, tests_dir


def run_f4pga_test(tf, config_files=list()):
    config_files_list = config_files + ["Makefile"]
    tf.backend.configure()
    tf.compare_files(config_files_list)


def test_f4pga(make_edalize_test):
    tool = "f4pga"
    tool_options = {
        "arch": "xilinx",
        "device_type": "artix7",
        "device_name": "xc7a50t_test",
        "part": "xc7a35tcpg236-1",
    }

    files = [{"name": "top.xdc", "file_type": "xdc"}]

    tf = make_edalize_test(
        "f4pga",
        test_name="test_f4pga_0",
        param_types=[],
        tool_options=tool_options,
        files=files,
        ref_dir="",
    )

    run_f4pga_test(tf)
