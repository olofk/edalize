import pytest
from .edalize_tool_common import tool_fixture


def test_tool_gowin_pack(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "routed.json", "file_type": "nextpnrRoutedJson"})

    tf = tool_fixture(
        "gowinpack",
        files=files,
        tool_options={"device": "GW1N-LV1QN48C6/I5"},
        ref_subdir="gowin",
    )

    tf.tool.configure()


def test_tool_gowin_pack_family(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "routed.json", "file_type": "nextpnrRoutedJson"})

    tf = tool_fixture(
        "gowinpack",
        files=files,
        tool_options={"device": "GW1NR-LV9QN88PC6/I5", "device_family": "GW1N-9C"},
        ref_subdir="gowin-family",
    )

    tf.tool.configure()


def test_tool_gowin_pack_no_input(tool_fixture):
    with pytest.raises(RuntimeError) as e:
        tool = tool_fixture(
            "gowinpack", files=[], tool_options={"device": "GW1N-LV1QN48C6/I5"}
        )
    assert "No input file specified for gowin_pack" in str(e.value)


def test_tool_gowin_pack_multiple_inputs(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "a.json", "file_type": "nextpnrRoutedJson"})
    files.append({"name": "b.json", "file_type": "nextpnrRoutedJson"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture(
            "gowinpack", files=files, tool_options={"device": "GW1N-LV1QN48C6/I5"}
        )
    assert "gowin_pack only supports one input file. Found a.json and b.json" in str(
        e.value
    )


def test_tool_gowin_pack_no_device(tool_fixture):
    from .edalize_tool_common import FILES

    files = FILES.copy()
    files.append({"name": "a.json", "file_type": "nextpnrRoutedJson"})

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("gowinpack", files=files)
    assert "No device or device family specified" in str(e.value)
