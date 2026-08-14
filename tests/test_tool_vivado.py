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


def test_tool_vivado_simulation_include_file(tool_fixture):
    """A simulation include file has to reach the next tool in the flow.

    Vivado itself never reads an include file into the project, but the
    simulator further down the flow still needs it.
    """
    files = [
        {"name": "top.v", "file_type": "verilogSource"},
        {
            "name": "defs.svh",
            "file_type": "systemVerilogSource",
            "is_include_file": True,
            "tags": ["simulation"],
        },
        {"name": "tb.sv", "file_type": "systemVerilogSource", "tags": ["simulation"]},
    ]

    tf = tool_fixture("vivado", files=files, paramtypes=[], has_makefile=False)
    tf.tool.configure()

    forwarded = [f["name"] for f in tf.tool.edam["files"]]
    assert "defs.svh" in forwarded
    assert "tb.sv" in forwarded

    # The include file is not part of the project, so it must not be named
    # in a get_files call that would match nothing
    tcl = (tf.tool.work_root / "design.tcl").read_text()
    assert "get_files defs.svh" not in tcl
    assert "get_files tb.sv" in tcl
