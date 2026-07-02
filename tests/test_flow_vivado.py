from .edalize_flow_common import flow_fixture


def test_vivado(flow_fixture):
    flow_options = {"part": "xc7a35tcsg324-1"}
    ff = flow_fixture("vivado", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.tcl",
            "design_netlist.tcl",
            "design_pgm.tcl",
            "design_run.tcl",
            "design_synth.tcl",
            "Makefile",
        ]
    )


def test_vivado_yosys_synth(flow_fixture):
    flow_options = {"part": "xc7a35tcsg324-1", "synth": "yosys"}
    ff = flow_fixture("vivado", flow_options=flow_options, ref_subdir="yosys")

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.tcl",
            "edalize_yosys_procs.tcl",
            "edalize_yosys_template.tcl",
            "Makefile",
        ]
    )
