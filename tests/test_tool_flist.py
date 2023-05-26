import pytest
from .edalize_tool_common import tool_fixture


def test_tool_flist(tool_fixture):
    from .edalize_tool_common import FILES

    tf = tool_fixture("flist")

    tf.tool.configure()
    tf.compare_config_files(["design.f"])
