import pytest
from .edalize_tool_common import tool_fixture


def test_tool_vpr(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "netlist.eblif", "file_type": "eblif"})

    tool_options = {"arch_xml": "/path/to/k6_N10_mem32K_40nm.xml"}

    tf = tool_fixture("vpr", tool_options=tool_options, files=files)

    tf.tool.configure()


def test_tool_vpr_generate_constraints(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "netlist.eblif", "file_type": "eblif"})

    tool_options = {
        "arch_xml": "/path/to/k6_N10_mem32K_40nm.xml",
        "generate_constraints": [
            "netlist.eblif",
            "design.net",
            "xc7a35tcpg236-1",
            "xc7a50t_test",
            "/path/to/k6_N10_mem32K_40nm.xml",
        ],
        "vpr_options": ["some", "vpr", "options"],
    }

    tf = tool_fixture(
        "vpr", tool_options=tool_options, files=files, ref_subdir="constraints"
    )

    tf.tool.configure()


def test_tool_vpr_multiple_netlists(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "a.eblif", "file_type": "eblif"})
    files.append({"name": "b.blif", "file_type": "blif"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("vpr", files=files)
    assert "VPR only supports one netlist file. Found a.eblif and b.blif" in str(
        e.value
    )
