# Register the shared fixtures for all test modules. Importing them into each
# module instead would shadow the fixture parameters of the same name.
pytest_plugins = [
    "tests.edalize_common",
    "tests.edalize_flow_common",
    "tests.edalize_tool_common",
]
