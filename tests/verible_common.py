FATALITY_OPTIONS = ("lint_fatal", "parse_fatal")


def assert_fatality_option_types(tool_options):
    actual_types = {option: tool_options[option]["type"] for option in FATALITY_OPTIONS}
    assert actual_types == {option: "bool" for option in FATALITY_OPTIONS}


def assert_fatality_arguments(command, expected_values):
    for option, value in expected_values.items():
        expected_argument = f"--{option}={'true' if value else 'false'}"
        assert command.count(expected_argument) == 1
