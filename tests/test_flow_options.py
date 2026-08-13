import logging

from .edalize_flow_common import flow_fixture


def test_unknown_flow_option_warns(flow_fixture, caplog):
    """An option that no tool in the flow accepts should not vanish silently."""
    flow_options = {"part": "xc7a35tcsg324-1", "definitely_not_an_option": "value"}

    with caplog.at_level(logging.WARNING, logger="edalize.flows.edaflow"):
        flow_fixture("vivado", flow_options=flow_options)

    assert (
        "Ignoring unknown option 'definitely_not_an_option' for flow 'vivado'"
        in caplog.text
    )


def test_misspelled_flow_option_is_suggested(flow_fixture, caplog):
    """A near miss of a real option should point at the option it resembles."""
    flow_options = {"part": "xc7a35tcsg324-1", "pgmm": True}

    with caplog.at_level(logging.WARNING, logger="edalize.flows.edaflow"):
        flow_fixture("vivado", flow_options=flow_options)

    assert "Ignoring unknown option 'pgmm' for flow 'vivado'" in caplog.text
    assert "Did you mean 'pgm'?" in caplog.text


def test_misspelled_tool_option_is_suggested(flow_fixture, caplog):
    """Tool options reach the flow through flow_options, so they count as valid."""
    flow_options = {"part": "xc7a35tcsg324-1", "jtag_freqq": 1000}

    with caplog.at_level(logging.WARNING, logger="edalize.flows.edaflow"):
        flow_fixture("vivado", flow_options=flow_options)

    assert "Did you mean 'jtag_freq'?" in caplog.text


def test_valid_flow_options_are_silent(flow_fixture, caplog):
    """Flow options, tool options and inherited options must not warn."""
    flow_options = {
        "part": "xc7a35tcsg324-1",  # vivado tool option
        "pgm": False,  # vivado flow option
        "frontends": [],  # inherited from Edaflow
        "flow_make_options": [],  # inherited from Edaflow
    }

    with caplog.at_level(logging.WARNING, logger="edalize.flows.edaflow"):
        flow_fixture("vivado", flow_options=flow_options)

    assert "Ignoring unknown option" not in caplog.text


def test_options_of_a_tool_not_in_the_graph_warn(flow_fixture, caplog):
    """Which options are valid depends on which tools the flow graph contains.

    yosys only joins the vivado flow when synth is set to yosys, so its
    options mean nothing here.
    """
    flow_options = {"part": "xc7a35tcsg324-1", "yosys_synth_options": ["-flatten"]}

    with caplog.at_level(logging.WARNING, logger="edalize.flows.edaflow"):
        flow_fixture("vivado", flow_options=flow_options)

    assert "Ignoring unknown option 'yosys_synth_options'" in caplog.text
