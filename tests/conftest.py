import os

# Register the shared fixtures for all test modules. Importing them into each
# module instead would shadow the fixture parameters of the same name.
pytest_plugins = [
    "tests.edalize_common",
    "tests.edalize_flow_common",
    "tests.edalize_tool_common",
]

# Make sure make does not pick up options like -jN from MAKEFLAGS. Several
# mock commands append to one .cmd file, so parallel make scrambles them.
# Done at import, not in a fixture: some tests rebind os.environ, after which
# changes no longer reach subprocesses.
os.environ.pop("MAKEFLAGS", None)
