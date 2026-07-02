from .edalize_flow_common import flow_fixture


def test_flow_vpr(flow_fixture):
    flow_options = {
        "arch": "xilinx",
        "arch_xml": "/path/to/k6_N10_mem32K_40nm.xml",
    }
    ff = flow_fixture("vpr", flow_options=flow_options)

    ff.flow.configure()
    ff.compare_config_files(
        [
            "Makefile",
        ]
    )
