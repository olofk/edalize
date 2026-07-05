# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pytest

from .edalize_tool_common import tool_fixture


def test_tool_xsim(tool_fixture) -> None:
    """Test the AMD/Xilinx XSim logic simulator backend."""
    tool_options = {
        "xelab_options": ["some", "xelab", "options"],
        "xsim_options": ["some", "xrun", "options"],
    }

    tf = tool_fixture("xsim", tool_options=tool_options)

    tf.tool.configure()
    tf.compare_config_files(
        [
            "xsim.prj",
        ]
    )

    cmd, args, _ = tf.tool.run()
    assert cmd == "xsim"
    assert "--runall" in args
    assert "--tclbatch" in args
    assert args[args.index("--tclbatch") + 1] == "tcl_file.tcl"
    assert args[-1] == "top_module"


def test_tool_xsim_minimal(tool_fixture) -> None:
    """Test the AMD/Xilinx XSim logic simulator backend."""
    tf = tool_fixture("xsim", tool_options={}, paramtypes=[], ref_subdir="minimal")

    tf.tool.configure()
    tf.compare_config_files(
        [
            "xsim.prj",
        ]
    )

    cmd, args, _ = tf.tool.run()
    assert cmd == "xsim"
    assert "--runall" in args
    assert "--tclbatch" in args
    assert args[args.index("--tclbatch") + 1] == "tcl_file.tcl"
    assert args[-1] == "top_module"


@pytest.mark.parametrize("gui", (None, False, True))
def test_tool_xsim_gui(tool_fixture, gui: bool | None) -> None:
    """Test if the AMD/Xilinx XSim logic simulator backend will add the ``-gui`` option."""
    tool_options = {}

    if gui is not None:
        tool_options["gui"] = gui

    tf = tool_fixture(
        "xsim", tool_options=tool_options, paramtypes=[], ref_subdir="minimal"
    )

    tf.tool.configure()

    cmd, args, _ = tf.tool.run()
    assert cmd == "xsim"

    if gui:
        assert "--gui" in args
        assert "--runall" not in args
    else:
        assert "--gui" not in args
        assert "--runall" in args

    assert "--tclbatch" in args
    assert args[args.index("--tclbatch") + 1] == "tcl_file.tcl"
    assert args[-1] == "top_module"
