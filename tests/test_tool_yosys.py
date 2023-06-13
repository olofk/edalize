import pytest

from .edalize_tool_common import tool_fixture


@pytest.mark.parametrize("arch", ["xilinx", "ice40", "ecp5"])
@pytest.mark.parametrize("output_format", ["json", "edif", "blif", "verilog"])
def test_tool_yosys(arch, output_format, tool_fixture):

    tool_options = {
        "arch": arch,
        "output_format": output_format,
        "yosys_synth_options": ["some", "yosys", "synth", "options"],
    }
    tf = tool_fixture(
        "yosys", tool_options=tool_options, ref_subdir=f"{arch}-{output_format}"
    )

    tf.tool.configure()
    tf.compare_config_files(["edalize_yosys_template.tcl", "edalize_yosys_procs.tcl"])


def test_tool_yosys_noarch(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tool = tool_fixture("yosys")
    assert "yosys requires tool option 'arch'" in str(e.value)


def test_tool_yosys_minimal(tool_fixture):
    tool_options = {"arch": "ice40"}

    tf = tool_fixture("yosys", tool_options=tool_options, ref_subdir="minimal")

    tf.tool.configure()
    tf.compare_config_files(["edalize_yosys_template.tcl", "edalize_yosys_procs.tcl"])


def test_tool_yosys_tags(tool_fixture):
    from .edalize_tool_common import FILES

    tool_options = {"arch": "ice40"}
    files = FILES.copy()
    files.append(
        {"name": "testbench.v", "file_type": "verilogSource", "tags": "simulation"}
    )

    tf = tool_fixture(
        "yosys", tool_options=tool_options, files=files, ref_subdir="minimal"
    )

    tf.tool.configure()
    tf.compare_config_files(["edalize_yosys_template.tcl", "edalize_yosys_procs.tcl"])


def test_tool_yosys_template(tool_fixture):
    import os

    tool_options = {"arch": "ice40", "yosys_template": "some_file.tcl"}

    tf = tool_fixture("yosys", tool_options=tool_options, ref_subdir="template")

    tf.tool.configure()
    tf.compare_config_files(["edalize_yosys_procs.tcl"])
    assert not os.path.exists(tf.tool.work_root / "edalize_yosys_template.tcl")
