from edalize.flows.edaflow import merge_edam


def test_merge_edam():
    common = [{"name": "common.v", "file_type": "verilogSource"}]
    a = {
        "name": "design",
        "files": common + [{"name": "a.v", "file_type": "verilogSource"}],
        "hooks": {"pre_build": [{"name": "s", "cmd": ["true"]}]},
        "tool_options": {"toola": {"opt": ["x"]}},
        "toplevel": "top",
    }
    b = {
        "name": "design",
        "files": common + [{"name": "b.v", "file_type": "verilogSource"}],
        "hooks": {"pre_build": [{"name": "s", "cmd": ["true"]}]},
        "tool_options": {"toolb": {"opt": ["y"]}},
        "toplevel": "top",
    }

    merged = merge_edam(a, b)

    # Files inherited from a common ancestor only appear once
    assert [f["name"] for f in merged["files"]] == ["common.v", "a.v", "b.v"]
    assert merged["hooks"]["pre_build"] == [{"name": "s", "cmd": ["true"]}]
    # Dicts are merged recursively
    assert merged["tool_options"] == {
        "toola": {"opt": ["x"]},
        "toolb": {"opt": ["y"]},
    }
    assert merged["name"] == "design"
    assert merged["toplevel"] == "top"

    # Inputs are not modified
    assert [f["name"] for f in a["files"]] == ["common.v", "a.v"]
    assert [f["name"] for f in b["files"]] == ["common.v", "b.v"]


def test_merge_edam_scalar_conflict():
    assert merge_edam({"toplevel": "a"}, {"toplevel": "b"})["toplevel"] == "b"


def test_merge_edam_empty():
    edam = {"name": "design", "files": [{"name": "a.v"}]}
    assert merge_edam({}, edam) == edam
