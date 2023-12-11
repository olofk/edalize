from .edalize_flow_common import flow_fixture


def test_lint(flow_fixture):
    flow_options = {"tool": "verilator"}
    ff = flow_fixture("lint", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "design.vc",
            "Makefile",
        ]
    )
