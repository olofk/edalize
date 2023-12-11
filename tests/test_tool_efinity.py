from .edalize_tool_common import tool_fixture


def test_tool_efinity(tool_fixture):
    import os

    tool_options = {"family": "Trion", "part": "T8F81", "timing": "C2"}

    orig_env = os.environ.copy()
    os.environ["EFINITY_HOME"] = "path/to/efinity/intallation"
    tf = tool_fixture("efinity", tool_options=tool_options)
    os.environ = orig_env

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            name + ".xml",
        ]
    )


def test_tool_efinity_no_env(tool_fixture):
    import pytest

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("efinity")
    assert "The environment variable EFINITY_HOME is not set" in str(e.value)
