from pathlib import Path

import pytest

from .edalize_common import compare_files
from .edalize_tool_common import get_edam, get_tool, tool_fixture

TLV_FILES = [{"name": "tlv_file.tlv", "file_type": "TLVerilogSource"}]

REF_DIR = Path(__file__).parent / "tools" / "sandpipersaas"


def _setup_sandpipersaas(tmp_path, tool_options={}):
    # sandpipersaas embeds work_root in the generated Makefile, so use a
    # fixed value instead of the tool_fixture default to keep the
    # reference file deterministic
    tool = get_tool("sandpipersaas")()
    edam = get_edam("sandpipersaas", tool_options=tool_options, files=TLV_FILES.copy())
    tool.work_root = "work_root"
    tool.setup(edam)
    tool.commands.write(tmp_path / "Makefile")
    return tool


def test_tool_sandpipersaas(tmp_path):
    tool = _setup_sandpipersaas(tmp_path)

    compare_files(REF_DIR, tmp_path, ["Makefile"])

    # The generated Verilog file is added to the output EDAM
    assert {"name": "design_tlv.v", "file_type": "verilogSource"} in tool.edam["files"]

    tool.run()


def test_tool_sandpipersaas_options(tmp_path):
    tool_options = {
        "sandpiper_saas": ["--default_makerchip_tlv"],
        "output_file": ["design.sv"],
        "output_dir": ["out"],
        "includes": ["include1.tlv", "include2.tlv"],
    }
    tool = _setup_sandpipersaas(tmp_path, tool_options=tool_options)

    compare_files(REF_DIR / "options", tmp_path, ["Makefile"])

    assert {
        "name": "out/design.sv",
        "file_type": "systemVerilogSource",
    } in tool.edam["files"]


def test_tool_sandpipersaas_multiple_files(tool_fixture):
    files = TLV_FILES + [
        {"name": "another_tlv_file.tlv", "file_type": "TLVerilogSource"}
    ]

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("sandpipersaas", files=files)
    assert "Only 1 TL-V top-level file is allowed" in str(e.value)


def test_tool_sandpipersaas_wrong_file_type(tool_fixture):
    files = [{"name": "vlog_file.v", "file_type": "verilogSource"}]

    with pytest.raises(RuntimeError) as e:
        tf = tool_fixture("sandpipersaas", files=files)
    assert "Expected file type: TLVerilogSource" in str(e.value)
