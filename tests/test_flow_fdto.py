from copy import deepcopy

from .edalize_flow_common import get_edam, get_flow


def build_flow(flow_name, flow_options, work_root):
    edam = get_edam(flow_options=flow_options)
    get_flow(flow_name)(edam, work_root)
    return edam


def test_flow_defined_tool_options_are_not_modified(tmp_path):
    """Flows pass class-level dicts as a node's flow-defined tool options.

    merge_dict updates its first argument in place, so merging the EDAM
    options into them used to write user options into the class.
    """
    Vivado = get_flow("vivado")
    before = deepcopy(Vivado.FLOW_DEFINED_TOOL_OPTIONS)

    build_flow(
        "vivado",
        {
            "part": "xc7a35tcsg324-1",
            "synth": "yosys",
            "yosys_synth_options": ["-nordff"],
        },
        tmp_path,
    )

    assert Vivado.FLOW_DEFINED_TOOL_OPTIONS == before


def fdto_of(flow_cls):
    return {k: v.get("fdto", {}) for k, v in flow_cls._flow.items()}


def test_flow_defined_tool_options_are_not_modified_by_nested_flow(tmp_path):
    """Flows that keep their graph in a class-level _flow dict behave the same."""
    Trellis = get_flow("trellis")
    before = deepcopy(fdto_of(Trellis))

    build_flow("trellis", {"nextpnr_options": ["--seed", "1"]}, tmp_path)

    assert fdto_of(Trellis) == before


def test_tool_options_do_not_leak_between_flows(tmp_path):
    """A flow must not inherit tool options set by an earlier one."""
    build_flow(
        "vivado",
        {
            "part": "xc7a35tcsg324-1",
            "synth": "yosys",
            "yosys_synth_options": ["-nordff"],
        },
        tmp_path,
    )

    edam = build_flow("vivado", {"part": "xc7a35tcsg324-1", "synth": "yosys"}, tmp_path)

    assert "yosys_synth_options" not in edam["tool_options"]["yosys"]


def test_list_tool_options_do_not_accumulate(tmp_path):
    """merge_dict concatenates lists, so a leak grew the list on every run."""
    for _ in range(3):
        edam = build_flow(
            "vivado",
            {
                "part": "xc7a35tcsg324-1",
                "synth": "yosys",
                "yosys_synth_options": ["-nordff"],
            },
            tmp_path,
        )

    assert edam["tool_options"]["yosys"]["yosys_synth_options"] == ["-nordff"]


def test_flow_defined_tool_options_still_reach_the_tool(tmp_path):
    """The copy must not stop the flow-defined options getting through."""
    edam = build_flow("vivado", {"part": "xc7a35tcsg324-1", "synth": "yosys"}, tmp_path)

    assert edam["tool_options"]["yosys"]["arch"] == "xilinx"
    assert edam["tool_options"]["yosys"]["output_format"] == "edif"
