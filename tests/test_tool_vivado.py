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
