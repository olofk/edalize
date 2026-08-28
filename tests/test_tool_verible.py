import pytest

from .edalize_tool_common import FILES, tool_fixture


def _command_args(tool):
    command = next(c for c in tool.commands.commands if c.targets == ["lint"])
    return command.commands[0]


def test_tool_verible_fatality_defaults(tool_fixture):
    from edalize.tools.verible import Verible

    tool_options = Verible.get_tool_options()
    assert tool_options["lint_fatal"]["type"] == "bool"
    assert tool_options["parse_fatal"]["type"] == "bool"

    tf = tool_fixture("verible")

    args = _command_args(tf.tool)
    assert args.count("--lint_fatal=true") == 1
    assert args.count("--parse_fatal=true") == 1


@pytest.mark.parametrize(
    "raw_arg",
    [
        "--lint_fatal",
        "--lint_fatal=true",
        "--lint_fatal=false",
        "--nolint_fatal",
        "--parse_fatal",
        "--parse_fatal=true",
        "--parse_fatal=false",
        "--noparse_fatal",
    ],
)
def test_tool_verible_rejects_raw_fatality_args(tool_fixture, raw_arg):
    with pytest.raises(RuntimeError, match="boolean tool options"):
        tool_fixture(
            "verible",
            tool_options={"verible_lint_args": [raw_arg]},
            has_makefile=False,
        )


def test_tool_verible_preserves_unrelated_raw_args(tool_fixture):
    tf = tool_fixture(
        "verible",
        tool_options={"verible_lint_args": ["--show_diagnostic_context"]},
        has_makefile=False,
    )

    assert _command_args(tf.tool).count("--show_diagnostic_context") == 1


def test_tool_verible_rules_and_ruleset(tool_fixture):
    tool_options = {
        "ruleset": "all",
        "rules": ["module-filename", "-line-length"],
        "verible_lint_args": ["--show_diagnostic_context"],
        "lint_fatal": False,
        "parse_fatal": False,
    }

    tool_fixture("verible", tool_options=tool_options, ref_subdir="options")


def test_tool_verible_selects_inputs_and_preserves_unrelated_files(tool_fixture):
    tf = tool_fixture("verible", has_makefile=False)

    args = _command_args(tf.tool)
    assert args[-5:] == [
        "sv_file.sv",
        "vlog_file.v",
        "vlog_with_define.v",
        "vlog05_file.v",
        "another_sv_file.sv",
    ]
    assert "vlog_incfile" not in args
    assert "--rules_config=config.vbl" in args
    assert "--waiver_files=verible_waiver.vbw,verible_waiver2.vbw" in args

    assert {"name": "qip_file.qip", "file_type": "QIP"} in tf.tool.edam["files"]


def test_tool_verible_omits_unsupported_parameters(tool_fixture):
    tf = tool_fixture("verible", has_makefile=False)

    args = [str(arg) for arg in _command_args(tf.tool)]
    assert not any(arg.startswith(("-D", "-G", "+define+")) for arg in args)
    assert not any("vlogdefine_" in arg or "vlogparam_" in arg for arg in args)


def test_tool_verible_rejects_multiple_rules_files(tool_fixture):
    files = FILES + [{"name": "another.vbl", "file_type": "veribleLintRules"}]

    with pytest.raises(RuntimeError, match="single rules file"):
        tool_fixture("verible", files=files, has_makefile=False)


def test_tool_verible_rejects_no_lintable_source(tool_fixture):
    files = [
        {"name": "config.vbl", "file_type": "veribleLintRules"},
        {"name": "timing.sdc", "file_type": "SDC"},
    ]

    with pytest.raises(RuntimeError, match="at least one"):
        tool_fixture("verible", files=files, has_makefile=False)
