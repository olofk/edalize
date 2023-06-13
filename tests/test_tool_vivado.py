from .edalize_tool_common import tool_fixture


def test_tool_vivado(tool_fixture):
    tf = tool_fixture("vivado")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + ".tcl",
            name + "_netlist.tcl",
            name + "_run.tcl",
            name + "_synth.tcl",
            name + "_pgm.tcl",
        ]
    )


def test_tool_vivado_tags(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append(
        {"name": "testbench.v", "file_type": "verilogSource", "tags": "simulation"}
    )

    tf = tool_fixture("vivado", files=files, ref_subdir="tags")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + ".tcl",
            name + "_netlist.tcl",
            name + "_run.tcl",
            name + "_synth.tcl",
            name + "_pgm.tcl",
        ]
    )
