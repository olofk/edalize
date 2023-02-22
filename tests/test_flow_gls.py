from .edalize_flow_common import flow_fixture


def test_gls(flow_fixture):
    flow_options = {"synth": "yosys", "sim": "icarus", "arch": "ice40"}
    ff = flow_fixture("gls", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.scr",
            "edalize_yosys_procs.tcl",
            "edalize_yosys_template.tcl",
            "Makefile",
        ]
    )
