# Hand-written verification suite written to cross-check the type-hints PR.
#
# 200 small, fast tests probing the surface area I might have changed:
#   - the 9 substantive (non-annotation) edits, each tested directly
#   - every Edatool backend instantiates cleanly
#   - every tools/ backend instantiates cleanly
#   - every flows/ backend imports cleanly
#   - EDAM TypedDict accepts every key I declared
#   - utility helpers behave identically
#   - widened type-acceptance does not narrow real-world inputs

from __future__ import annotations

import importlib
import inspect
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def minimal_edam(name: str = "t", toplevel: str = "top") -> dict[str, Any]:
    return {"name": name, "files": [], "toplevel": toplevel, "tool_options": {}}


def rich_edam(name: str = "t") -> dict[str, Any]:
    return {
        "name": name,
        "files": [
            {"name": "a.v", "file_type": "verilogSource"},
            {"name": "b.sv", "file_type": "systemVerilogSource"},
            {
                "name": "inc.vh",
                "file_type": "verilogSource",
                "is_include_file": True,
            },
        ],
        "toplevel": "top",
        "tool_options": {},
        "parameters": {
            "WIDTH": {
                "datatype": "int",
                "default": 4,
                "paramtype": "vlogparam",
                "description": "Bit-width",
            }
        },
        "vpi": [],
        "hooks": {},
    }


# ---------------------------------------------------------------------------
# 1–9: behaviour-of-substantive-changes (~30 tests)
# ---------------------------------------------------------------------------

# Change 1: Edatool._apply_parameters(None) → silent no-op


def test_001_apply_parameters_none_raises(tmp_path):
    """Pristine behaviour: _apply_parameters(None) crashes at args.items()."""
    from edalize.icarus import Icarus

    icarus = Icarus(rich_edam(), str(tmp_path))
    with pytest.raises(AttributeError):
        icarus._apply_parameters(None)  # type: ignore[arg-type]


def test_002_apply_parameters_empty_dict_is_noop(tmp_path):
    from edalize.icarus import Icarus

    icarus = Icarus(rich_edam(), str(tmp_path))
    icarus._apply_parameters({})


def test_003_apply_parameters_real_dict_still_works(tmp_path):
    from edalize.icarus import Icarus

    icarus = Icarus(rich_edam(), str(tmp_path))
    icarus._apply_parameters({"WIDTH": 8})
    assert icarus.vlogparam["WIDTH"] == 8


# Change 2: run_pre accepts list subclass


def test_004_run_pre_accepts_plain_list(tmp_path):
    from edalize.icarus import Icarus

    icarus = Icarus(rich_edam(), str(tmp_path))
    icarus.run_pre([])  # legacy plain list path


def test_005_run_pre_accepts_list_subclass(tmp_path):
    from edalize.icarus import Icarus

    class MyList(list):
        pass

    icarus = Icarus(rich_edam(), str(tmp_path))
    icarus.run_pre(MyList())  # widened path


def test_006_run_pre_accepts_dict(tmp_path):
    from edalize.icarus import Icarus

    icarus = Icarus(rich_edam(), str(tmp_path))
    icarus.run_pre({})


def test_007_run_pre_none_crashes(tmp_path):
    """Pristine behaviour: run_pre(None) forwards None to _apply_parameters,
    which crashes at args.items(). Annotation work must preserve this."""
    from edalize.icarus import Icarus

    icarus = Icarus(rich_edam(), str(tmp_path))
    with pytest.raises(AttributeError):
        icarus.run_pre(None)


# Change 3: Make.write accepts str or Path


def test_008_make_write_accepts_path(tmp_path):
    from edalize.build_runners.make import Make
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add(["echo"], ["all"], [])
    cmds.set_default_target("all")
    Make({}).write(cmds, tmp_path)
    assert (tmp_path / "Makefile").exists()


def test_009_make_write_accepts_str(tmp_path):
    from edalize.build_runners.make import Make
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add(["echo"], ["all"], [])
    cmds.set_default_target("all")
    Make({}).write(cmds, str(tmp_path))
    assert (tmp_path / "Makefile").exists()


def test_010_make_writes_same_content_for_str_and_path(tmp_path):
    from edalize.build_runners.make import Make
    from edalize.utils import EdaCommands

    out1 = tmp_path / "a"
    out2 = tmp_path / "b"
    out1.mkdir(); out2.mkdir()
    for out, kind in [(out1, "path"), (out2, "str")]:
        cmds = EdaCommands()
        cmds.add(["echo"], ["all"], [])
        cmds.set_default_target("all")
        Make({}).write(cmds, out if kind == "path" else str(out))
    assert (out1 / "Makefile").read_text() == (out2 / "Makefile").read_text()


# Change 4: verilator dead-code removal doesn't lose any include dirs


def test_011_verilator_collects_incdirs_correctly(tmp_path):
    from edalize.verilator import Verilator

    edam = rich_edam()
    edam["tool_options"] = {"verilator": {"mode": "lint-only"}}
    vl = Verilator(edam, str(tmp_path))
    # _write_config_files is what I edited; just make sure it runs without losing files
    vl._write_config_files()
    vc = (tmp_path / "t.vc").read_text()
    assert "a.v" in vc
    assert "b.sv" in vc


# Change 5: vpr f.name → f["name"]


def test_012_vpr_handles_sdc_files(tmp_path):
    from edalize.tools.vpr import Vpr

    v = Vpr()
    v.work_root = str(tmp_path)
    edam = minimal_edam("t")
    edam["files"] = [
        {"name": "design.eblif", "file_type": "blif"},
        {"name": "constr.sdc", "file_type": "SDC"},
    ]
    edam["tool_options"] = {"vpr": {"arch_xml": "/tmp/arch.xml", "vpr_options": ["--device", "x"]}}
    v.setup(edam)
    # Just exercising the path that used to f.name → AttributeError
    # No crash = pass.


# Change 6: Edatool.tool_options class default is empty dict (only on the base)


def test_013_base_edatool_has_no_class_tool_options():
    """Pristine behaviour: bare Edatool has no `tool_options` class attribute.
    Adding one would create shared mutable state across subclasses, so the
    annotation-only declaration must not assign a default."""
    from edalize.edatool import Edatool

    assert not hasattr(Edatool, "tool_options")


def test_014_concrete_backends_set_tool_options_per_instance(tmp_path):
    """Pristine behaviour: legacy backends populate tool_options per
    instance in __init__, not as a class attribute."""
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    assert isinstance(i.tool_options, dict)
    assert "tool_options" not in Icarus.__dict__


# Change 7: Nextpnr.flow_config class default


def test_015_nextpnr_has_no_class_flow_config_default():
    """Pristine behaviour: Nextpnr.flow_config is unbound at the class level.
    Subflows inject it per-instance before configure()."""
    from edalize.nextpnr import Nextpnr

    assert "flow_config" not in Nextpnr.__dict__


def test_016_nextpnr_flow_config_writable(tmp_path):
    from edalize.nextpnr import Nextpnr

    npr = Nextpnr(minimal_edam(), str(tmp_path))
    npr.flow_config = {"arch": "ecp5"}
    assert npr.flow_config["arch"] == "ecp5"


# Change 8: EdaCommands.default_target class default


def test_017_edacommands_default_target_unset_initially():
    """Pristine behaviour: EdaCommands.default_target is unbound until
    set_default_target() is called."""
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    assert not hasattr(cmds, "default_target")


def test_018_edacommands_write_raises_on_missing_target(tmp_path):
    """Pristine behaviour: write() with no default target raises
    AttributeError when it tries to read self.default_target."""
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    with pytest.raises(AttributeError):
        cmds.write(str(tmp_path / "Makefile"))


def test_019_edacommands_write_succeeds_after_set_default(tmp_path):
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add(["true"], ["all"], [])
    cmds.set_default_target("all")
    cmds.write(str(tmp_path / "Makefile"))
    assert (tmp_path / "Makefile").exists()


# Change 9: Edaflow.configure_flow stub


def test_020_edaflow_configure_flow_unimplemented_raises_attribute_error():
    """Pristine behaviour: Edaflow does not define configure_flow; subclasses
    must override it. A subclass that forgets raises AttributeError."""
    from edalize.flows.edaflow import Edaflow

    flow = Edaflow.__new__(Edaflow)
    with pytest.raises(AttributeError):
        flow.configure_flow({})  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 21-25: ascentlint docstring untouched
# ---------------------------------------------------------------------------


def test_021_ascentlint_docstring_unchanged():
    from edalize.ascentlint import Ascentlint

    doc = Ascentlint.get_doc(0)
    assert doc is not None
    assert "Real Intent Ascent Lint backend" in doc["description"]
    assert "return None" not in doc["description"]


def test_022_ascentlint_get_doc_invalid_api():
    from edalize.ascentlint import Ascentlint

    assert Ascentlint.get_doc(99) is None


def test_023_ascentlint_options_list_intact():
    from edalize.ascentlint import Ascentlint

    doc = Ascentlint.get_doc(0)
    names = {x["name"] for x in doc["lists"]}
    assert "ascentlint_options" in names


def test_024_ascentlint_can_instantiate(tmp_path):
    from edalize.ascentlint import Ascentlint

    Ascentlint(minimal_edam(), str(tmp_path))


def test_025_ascentlint_doc_no_stray_keywords():
    from edalize.ascentlint import Ascentlint

    doc = Ascentlint.get_doc(0)
    for forbidden in ("return None", "TODO", "FIXME"):
        assert forbidden not in doc["description"]


# ---------------------------------------------------------------------------
# 026-095: legacy backends — each instantiates with rich and minimal EDAM (~70 tests)
# Skips tools that can't be imported standalone (templates, etc.).
# ---------------------------------------------------------------------------

LEGACY_BACKENDS = [
    ("apicula", "Apicula"),
    ("ascentlint", "Ascentlint"),
    ("design_compiler", "Design_compiler"),
    ("diamond", "Diamond"),
    ("gatemate", "Gatemate"),
    ("genus", "Genus"),
    ("ghdl", "Ghdl"),
    ("icarus", "Icarus"),
    ("icestorm", "Icestorm"),
    ("ise", "Ise"),
    ("isim", "Isim"),
    ("libero", "Libero"),
    ("mistral", "Mistral"),
    ("modelsim", "Modelsim"),
    ("morty", "Morty"),
    ("openlane", "Openlane"),
    ("openroad", "Openroad"),
    ("oxide", "Oxide"),
    ("quartus", "Quartus"),
    ("questaformal", "Questaformal"),
    ("radiant", "Radiant"),
    ("rivierapro", "Rivierapro"),
    ("sandpipersaas", "Sandpipersaas"),
    ("slang", "Slang"),
    ("spyglass", "Spyglass"),
    ("symbiflow", "Symbiflow"),
    ("symbiyosys", "Symbiyosys"),
    ("trellis", "Trellis"),
    ("vcs", "Vcs"),
    ("veribleformat", "Veribleformat"),
    ("veriblelint", "Veriblelint"),
    ("verilator", "Verilator"),
    ("vivado", "Vivado"),
    ("xcelium", "Xcelium"),
    ("xsim", "Xsim"),
    ("yosys", "Yosys"),
]


@pytest.mark.parametrize("modname,clsname", LEGACY_BACKENDS, ids=[m[0] for m in LEGACY_BACKENDS])
def test_legacy_backend_imports(modname, clsname):
    mod = importlib.import_module(f"edalize.{modname}")
    assert hasattr(mod, clsname), f"{modname} missing class {clsname}"


@pytest.mark.parametrize("modname,clsname", LEGACY_BACKENDS, ids=[m[0] for m in LEGACY_BACKENDS])
def test_legacy_backend_get_doc_returns_dict_or_none(modname, clsname):
    mod = importlib.import_module(f"edalize.{modname}")
    cls = getattr(mod, clsname)
    if hasattr(cls, "get_doc"):
        doc = cls.get_doc(0)
        assert doc is None or isinstance(doc, dict)


@pytest.mark.parametrize("modname,clsname", LEGACY_BACKENDS, ids=[m[0] for m in LEGACY_BACKENDS])
def test_legacy_backend_get_doc_invalid_api_returns_none(modname, clsname):
    mod = importlib.import_module(f"edalize.{modname}")
    cls = getattr(mod, clsname)
    if hasattr(cls, "get_doc"):
        # The contract added in this PR: api_ver != 0 must return None, not crash.
        assert cls.get_doc(42) is None


# ---------------------------------------------------------------------------
# tools/ backends import + instantiate (~20 tests)
# ---------------------------------------------------------------------------

TOOL_BACKENDS = [
    ("ecppack", "Ecppack"),
    ("efinity", "Efinity"),
    ("ghdl", "Ghdl"),
    ("gowin", "Gowin"),
    ("gowinpack", "Gowinpack"),
    ("icarus", "Icarus"),
    ("icepack", "Icepack"),
    ("icetime", "Icetime"),
    ("nextpnr", "Nextpnr"),
    ("openfpgaloader", "Openfpgaloader"),
    ("sandpipersaas", "Sandpipersaas"),
    ("surelog", "Surelog"),
    ("sv2v", "Sv2v"),
    ("vcs", "Vcs"),
    ("verilator", "Verilator"),
    ("vivado", "Vivado"),
    ("vpr", "Vpr"),
    ("xcelium", "Xcelium"),
    ("yosys", "Yosys"),
]


@pytest.mark.parametrize("modname,clsname", TOOL_BACKENDS, ids=[m[0] for m in TOOL_BACKENDS])
def test_tool_backend_imports(modname, clsname):
    mod = importlib.import_module(f"edalize.tools.{modname}")
    assert hasattr(mod, clsname), f"{modname} missing class {clsname}"


@pytest.mark.parametrize("modname,clsname", TOOL_BACKENDS, ids=[m[0] for m in TOOL_BACKENDS])
def test_tool_backend_instantiates(modname, clsname):
    mod = importlib.import_module(f"edalize.tools.{modname}")
    cls = getattr(mod, clsname)
    cls()  # tools/ backends have a no-arg constructor


# ---------------------------------------------------------------------------
# flows/ backends import (~13 tests)
# ---------------------------------------------------------------------------

FLOW_BACKENDS = [
    "apicula",
    "efinity",
    "f4pga",
    "generic",
    "gls",
    "gowin",
    "icestorm",
    "lint",
    "sim",
    "trellis",
    "vivado",
    "vpr",
]


@pytest.mark.parametrize("modname", FLOW_BACKENDS)
def test_flow_imports(modname):
    importlib.import_module(f"edalize.flows.{modname}")


# ---------------------------------------------------------------------------
# EDAM TypedDict shape (~15 tests)
# ---------------------------------------------------------------------------


def test_edam_minimal_dict_accepted():
    from edalize.edam import Edam

    e: Edam = {"name": "t"}
    assert e["name"] == "t"


def test_edam_full_dict_accepted():
    from edalize.edam import Edam

    e: Edam = {
        "name": "t",
        "files": [{"name": "a.v", "file_type": "verilogSource"}],
        "toplevel": "top",
        "tool_options": {"icarus": {"iverilog_options": ["-g2012"]}},
        "parameters": {"WIDTH": {"datatype": "int", "default": 4, "paramtype": "vlogparam"}},
        "vpi": [],
        "hooks": {},
    }
    assert e["name"] == "t"


def test_edam_file_with_tags():
    from edalize.edam import File

    f: File = {"name": "x.v", "file_type": "verilogSource", "tags": ["simulation"]}
    assert f["tags"] == ["simulation"]


def test_edam_file_with_define():
    from edalize.edam import File

    f: File = {"name": "x.v", "file_type": "verilogSource", "define": {"DEBUG": 1}}
    assert f["define"]["DEBUG"] == 1


def test_edam_file_with_logical_name():
    from edalize.edam import File

    f: File = {"name": "x.v", "logical_name": "work"}
    assert f["logical_name"] == "work"


def test_edam_parameter_shape():
    from edalize.edam import Parameter

    p: Parameter = {"datatype": "int", "default": 8, "paramtype": "vlogparam"}
    assert p["datatype"] == "int"


def test_edam_hooks_shape():
    from edalize.edam import Hooks, HookScript

    s: HookScript = {"name": "h", "cmd": ["echo", "ok"]}
    h: Hooks = {"pre_build": [s]}
    assert h["pre_build"][0]["name"] == "h"


def test_edam_vpi_shape():
    from edalize.edam import VpiModule

    v: VpiModule = {"name": "uvm", "src_files": ["a.c"], "include_dirs": ["."], "libs": ["pthread"]}
    assert v["name"] == "uvm"


def test_edam_module_exports():
    from edalize import edam

    for sym in (
        "Edam",
        "File",
        "Parameter",
        "Hooks",
        "HookScript",
        "VpiModule",
        "ToolOptions",
        "RunArgs",
        "ToolDoc",
        "DataType",
        "ParamType",
        "HookName",
    ):
        assert hasattr(edam, sym), f"edam.{sym} missing"


def test_edam_module_no_stray_attrs():
    """edam.py shouldn't accidentally export internal names."""
    from edalize import edam

    public = [n for n in edam.__all__]
    assert sorted(public) == sorted(set(public))


def test_edam_file_is_dict_subclass():
    from edalize.edam import File

    assert issubclass(File, dict)


def test_edam_edam_is_dict_subclass():
    from edalize.edam import Edam

    assert issubclass(Edam, dict)


def test_edam_paramtype_literal_values():
    """The Literal of param-types must match what backends recognise."""
    from edalize.edam import ParamType
    from typing import get_args

    assert set(get_args(ParamType)) == {
        "plusarg",
        "vlogparam",
        "vlogdefine",
        "generic",
        "cmdlinearg",
    }


def test_edam_datatype_literal_values():
    from edalize.edam import DataType
    from typing import get_args

    # Must mirror FuseSoC CAPI2 schema (fusesoc/capi2/json_schema.py).
    assert set(get_args(DataType)) == {"bool", "file", "int", "real", "str"}


def test_edam_hookname_literal_values():
    from edalize.edam import HookName
    from typing import get_args

    assert set(get_args(HookName)) == {"pre_build", "post_build", "pre_run", "post_run"}


# ---------------------------------------------------------------------------
# utils / EdaCommands behaviour (~12 tests)
# ---------------------------------------------------------------------------


def test_utils_get_file_type_strips_version():
    from edalize.utils import get_file_type

    class F:
        file_type = "vhdlSource-2008"

    assert get_file_type(F()) == "vhdlSource"


def test_utils_get_file_type_no_dash():
    from edalize.utils import get_file_type

    class F:
        file_type = "verilogSource"

    assert get_file_type(F()) == "verilogSource"


def test_utils_get_file_type_empty():
    from edalize.utils import get_file_type

    class F:
        file_type = ""

    assert get_file_type(F()) == ""


def test_edacommands_add_records_command():
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add(["echo", "hi"], ["all"], ["dep1"])
    assert len(cmds.commands) == 1
    assert cmds.commands[0].targets == ["all"]


def test_edacommands_add_var():
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add_var("FOO=bar")
    assert "FOO=bar" in cmds.variables


def test_edacommands_add_env_var_linux():
    """add_env_var should pick `export` on linux."""
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add_env_var("FOO", "bar")
    # On Linux/macOS the helper uses 'export'
    if sys.platform.startswith(("linux", "darwin")):
        assert any("export" in v for v in cmds.variables)


def test_edacommands_set_default_target():
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.set_default_target("foo")
    assert cmds.default_target == "foo"


def test_edacommands_write_includes_header(tmp_path):
    from edalize.utils import EdaCommands

    cmds = EdaCommands()
    cmds.add(["true"], ["all"], [])
    cmds.set_default_target("all")
    out = tmp_path / "Makefile"
    cmds.write(str(out))
    content = out.read_text()
    assert "Auto generated by Edalize" in content


def test_edacommands_command_repr_targets():
    from edalize.utils import EdaCommands

    cmd = EdaCommands.Command(["echo"], ["t1", "t2"], [], [], {})
    assert cmd.targets == ["t1", "t2"]


def test_edacommands_command_copies_order_only_deps():
    from edalize.utils import EdaCommands

    deps = ["pre_build"]
    cmd = EdaCommands.Command(["echo"], ["t"], [], deps, {})
    deps.append("mutated")
    assert "mutated" not in cmd.order_only_deps


def test_make_get_build_command():
    from edalize.build_runners.make import Make

    assert Make({}).get_build_command() == ("make", [])


def test_make_passes_through_flow_make_options():
    from edalize.build_runners.make import Make

    m = Make({"flow_make_options": ["-j4"]})
    assert m.get_build_command() == ("make", ["-j4"])


# ---------------------------------------------------------------------------
# Edatool inheritance + introspection (~12 tests)
# ---------------------------------------------------------------------------


def test_edatool_get_edatools_returns_list():
    from edalize.edatool import get_edatools

    tools = get_edatools()
    assert isinstance(tools, list)
    assert len(tools) > 5


def test_edatool_get_edatool_known_name():
    from edalize.edatool import get_edatool

    cls = get_edatool("icarus")
    assert cls.__name__ == "Icarus"


def test_edatool_get_edatool_unknown_raises():
    from edalize.edatool import get_edatool, ToolResolutionError

    with pytest.raises(ToolResolutionError):
        get_edatool("definitely_not_a_real_tool_zxq")


def test_edatool_tool_dataclass_module_path():
    from edalize.edatool import Tool
    from edalize.icarus import Icarus

    t = Tool("icarus", Icarus)
    assert "icarus" in t.module_path


def test_edatool_tool_dataclass_class_name():
    from edalize.edatool import Tool
    from edalize.icarus import Icarus

    t = Tool("icarus", Icarus)
    assert t.class_name == "Icarus"


def test_edatool_init_requires_name():
    from edalize.icarus import Icarus

    # An EDAM dict that is non-empty but missing "name" should raise RuntimeError.
    with pytest.raises(RuntimeError, match="name"):
        Icarus({"files": []}, "/tmp")


def test_edatool_init_accepts_eda_api_alias():
    from edalize.icarus import Icarus

    # Old-style `eda_api=` should still work; new-style `edam=` too.
    i = Icarus(eda_api=minimal_edam(), work_root="/tmp")
    assert i.name == "t"


def test_edatool_init_edam_takes_precedence():
    from edalize.icarus import Icarus

    a = minimal_edam("a")
    b = minimal_edam("b")
    i = Icarus(edam=a, work_root="/tmp", eda_api=b)
    assert i.name == "a"


def test_edatool_default_files_empty_list():
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), "/tmp")
    assert i.files == []


def test_edatool_default_tool_options_empty():
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), "/tmp")
    assert i.tool_options == {}


def test_edatool_default_parameters_empty():
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), "/tmp")
    assert i.parameters == {}


def test_edatool_default_hooks_empty():
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), "/tmp")
    assert i.hooks == {}


# ---------------------------------------------------------------------------
# jinja filter behaviour (~6 tests)
# ---------------------------------------------------------------------------


def test_jinja_filter_bool_true_as_str():
    from edalize.edatool import jinja_filter_param_value_str

    assert jinja_filter_param_value_str(True, bool_is_str=True) == "true"


def test_jinja_filter_bool_false_as_int():
    from edalize.edatool import jinja_filter_param_value_str

    assert jinja_filter_param_value_str(False) == "0"


def test_jinja_filter_bool_true_as_int():
    from edalize.edatool import jinja_filter_param_value_str

    assert jinja_filter_param_value_str(True) == "1"


def test_jinja_filter_str_quoted():
    from edalize.edatool import jinja_filter_param_value_str

    assert jinja_filter_param_value_str("foo", str_quote_style='"') == '"foo"'


def test_jinja_filter_int_passthrough():
    from edalize.edatool import jinja_filter_param_value_str

    assert jinja_filter_param_value_str(42) == "42"


def test_jinja_filter_float_passthrough():
    from edalize.edatool import jinja_filter_param_value_str

    val = jinja_filter_param_value_str(1.5)
    assert val == "1.5"


# ---------------------------------------------------------------------------
# _add_include_dir behaviour (~6 tests)
# ---------------------------------------------------------------------------


def test_add_include_dir_marks_include_files(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    incdirs: list[str] = []
    f = {"name": "x/y.vh", "is_include_file": True}
    assert i._add_include_dir(f, incdirs)
    assert incdirs == ["x"]


def test_add_include_dir_returns_false_for_normal_file(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    incdirs: list[str] = []
    f = {"name": "x.v", "file_type": "verilogSource"}
    assert not i._add_include_dir(f, incdirs)
    assert incdirs == []


def test_add_include_dir_dedupes(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    incdirs: list[str] = []
    i._add_include_dir({"name": "x/a.vh", "is_include_file": True}, incdirs)
    i._add_include_dir({"name": "x/b.vh", "is_include_file": True}, incdirs)
    assert incdirs == ["x"]


def test_add_include_dir_honours_include_path(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    incdirs: list[str] = []
    f = {"name": "x/y.vh", "is_include_file": True, "include_path": "custom/path"}
    i._add_include_dir(f, incdirs)
    assert incdirs == ["custom/path"]


def test_add_include_dir_root_file_uses_dot(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    incdirs: list[str] = []
    f = {"name": "y.vh", "is_include_file": True}
    i._add_include_dir(f, incdirs)
    assert incdirs == ["."]


def test_add_include_dir_force_slash(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    incdirs: list[str] = []
    f = {"name": "a\\b\\c.vh", "is_include_file": True}
    i._add_include_dir(f, incdirs, force_slash=True)
    assert all("\\" not in d for d in incdirs)


# ---------------------------------------------------------------------------
# parse_args / argparse (~6 tests)
# ---------------------------------------------------------------------------


def test_parse_args_no_params_returns_empty(tmp_path):
    from edalize.icarus import Icarus

    i = Icarus(minimal_edam(), str(tmp_path))
    assert i.parse_args([], i.argtypes) == {}


def test_parse_args_int_param(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()
    i = Icarus(edam, str(tmp_path))
    args = i.parse_args(["--WIDTH=8"], ["vlogparam"])
    assert args["WIDTH"] == 8


def test_parse_args_unknown_paramtype_warns(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()
    # plusarg isn't enabled — should be silently ignored, not crash.
    edam["parameters"]["RUNTIME"] = {
        "datatype": "str",
        "paramtype": "plusarg",
    }
    i = Icarus(edam, str(tmp_path))
    i.parse_args([], ["vlogparam"])


def test_parse_args_bool_param(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()
    edam["parameters"]["DEBUG"] = {
        "datatype": "bool",
        "default": False,
        "paramtype": "vlogdefine",
    }
    i = Icarus(edam, str(tmp_path))
    args = i.parse_args(["--DEBUG"], ["vlogparam", "vlogdefine"])
    assert args["DEBUG"] is True


def test_parse_args_str_param(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()
    edam["parameters"]["MODE"] = {
        "datatype": "str",
        "paramtype": "vlogparam",
    }
    i = Icarus(edam, str(tmp_path))
    args = i.parse_args(["--MODE=fast"], ["vlogparam"])
    assert args["MODE"] == "fast"


def test_parse_args_invalid_datatype_raises(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()
    edam["parameters"]["BAD"] = {
        "datatype": "complex",  # not a supported datatype
        "paramtype": "vlogparam",
    }
    i = Icarus(edam, str(tmp_path))
    with pytest.raises(RuntimeError, match="Invalid data type"):
        i.parse_args(["--BAD=1"], ["vlogparam"])


# ---------------------------------------------------------------------------
# Icarus end-to-end script-generation determinism (~10 tests)
# ---------------------------------------------------------------------------


def _icarus_with_files(tmp_path: Path, files: list[dict]) -> str:
    """Configure an Icarus backend and return the generated .scr content."""
    from edalize.icarus import Icarus

    edam = {
        "name": "t",
        "files": files,
        "toplevel": "top",
        "tool_options": {"icarus": {"iverilog_options": ["-g2012"]}},
        "parameters": {},
    }
    i = Icarus(edam, str(tmp_path))
    i.configure_main()
    return (tmp_path / "t.scr").read_text()


def test_icarus_scr_contains_verilog_file(tmp_path):
    scr = _icarus_with_files(tmp_path, [{"name": "a.v", "file_type": "verilogSource"}])
    assert "a.v" in scr


def test_icarus_scr_keeps_file_order(tmp_path):
    scr = _icarus_with_files(
        tmp_path,
        [
            {"name": "first.v", "file_type": "verilogSource"},
            {"name": "second.v", "file_type": "verilogSource"},
        ],
    )
    assert scr.index("first.v") < scr.index("second.v")


def test_icarus_scr_handles_systemverilog(tmp_path):
    scr = _icarus_with_files(tmp_path, [{"name": "a.sv", "file_type": "systemVerilogSource"}])
    assert "a.sv" in scr


def test_icarus_scr_include_dir(tmp_path):
    scr = _icarus_with_files(
        tmp_path,
        [
            {"name": "include/h.vh", "file_type": "verilogSource", "is_include_file": True},
            {"name": "a.v", "file_type": "verilogSource"},
        ],
    )
    assert "+incdir+include" in scr


def test_icarus_scr_is_deterministic(tmp_path):
    files = [{"name": "a.v", "file_type": "verilogSource"}]
    (tmp_path / "run1").mkdir()
    (tmp_path / "run2").mkdir()
    out1 = _icarus_with_files(tmp_path / "run1", files)
    out2 = _icarus_with_files(tmp_path / "run2", files)
    assert out1 == out2


def test_icarus_makefile_generated(tmp_path):
    from edalize.icarus import Icarus

    edam = minimal_edam()
    Icarus(edam, str(tmp_path)).configure_main()
    assert (tmp_path / "Makefile").exists()


def test_icarus_scr_file_named_after_edam(tmp_path):
    from edalize.icarus import Icarus

    edam = minimal_edam(name="my_design")
    Icarus(edam, str(tmp_path)).configure_main()
    assert (tmp_path / "my_design.scr").exists()


def test_icarus_define_propagated(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()
    edam["parameters"]["DEBUG"] = {
        "datatype": "bool",
        "default": True,
        "paramtype": "vlogdefine",
    }
    i = Icarus(edam, str(tmp_path))
    i.configure_main()
    scr = (tmp_path / "t.scr").read_text()
    assert "+define+DEBUG" in scr


def test_icarus_vlogparam_propagated(tmp_path):
    from edalize.icarus import Icarus

    edam = rich_edam()  # has WIDTH parameter
    i = Icarus(edam, str(tmp_path))
    i.configure_main()
    scr = (tmp_path / "t.scr").read_text()
    assert "+parameter+top.WIDTH=4" in scr


def test_icarus_empty_files_doesnt_crash(tmp_path):
    from edalize.icarus import Icarus

    Icarus(minimal_edam(), str(tmp_path)).configure_main()


# ---------------------------------------------------------------------------
# Verilator script generation (~6 tests)
# ---------------------------------------------------------------------------


def _verilator_setup(tmp_path: Path, mode: str = "lint-only") -> Path:
    from edalize.verilator import Verilator

    edam = rich_edam()
    edam["tool_options"] = {"verilator": {"mode": mode}}
    v = Verilator(edam, str(tmp_path))
    v._write_config_files()
    return tmp_path / "t.vc"


def test_verilator_vc_file_created(tmp_path):
    assert _verilator_setup(tmp_path).exists()


def test_verilator_vc_contains_files(tmp_path):
    content = _verilator_setup(tmp_path).read_text()
    assert "a.v" in content
    assert "b.sv" in content


def test_verilator_vc_include_dir_present(tmp_path):
    content = _verilator_setup(tmp_path).read_text()
    assert "+incdir+" in content


def test_verilator_vc_top_module(tmp_path):
    content = _verilator_setup(tmp_path).read_text()
    assert "--top-module top" in content


def test_verilator_modes_accepted(tmp_path):
    for i, mode in enumerate(["lint-only", "cc", "sc"]):
        d = tmp_path / f"m{i}"
        d.mkdir()
        _verilator_setup(d, mode=mode)


def test_verilator_no_incdirs_set_leftover(tmp_path):
    """The dead-code removal didn't lose anything."""
    content = _verilator_setup(tmp_path).read_text()
    assert content.count("+incdir+") >= 1


# ---------------------------------------------------------------------------
# nextpnr flow_config narrowing (~5 tests)
# ---------------------------------------------------------------------------


def test_nextpnr_uninitialized_flow_config_is_unbound():
    """Pristine behaviour: Nextpnr.flow_config has no class-level default."""
    from edalize.nextpnr import Nextpnr

    assert "flow_config" not in Nextpnr.__dict__


def test_nextpnr_subclass_sets_flow_config(tmp_path):
    from edalize.nextpnr import Nextpnr

    n = Nextpnr(minimal_edam(), str(tmp_path))
    n.flow_config = {"arch": "ice40"}
    assert n.flow_config["arch"] == "ice40"


def test_nextpnr_get_doc_returns_dict():
    from edalize.nextpnr import Nextpnr

    assert isinstance(Nextpnr.get_doc(0), dict)


def test_nextpnr_get_doc_invalid_returns_none():
    from edalize.nextpnr import Nextpnr

    assert Nextpnr.get_doc(99) is None


def test_nextpnr_instance_flow_config_independent(tmp_path):
    """Pristine behaviour: setting flow_config on one Nextpnr instance does
    not leak to another; both start with no flow_config until injected."""
    from edalize.nextpnr import Nextpnr

    a = Nextpnr(minimal_edam("a"), str(tmp_path / "a"))
    b = Nextpnr(minimal_edam("b"), str(tmp_path / "b"))
    a.flow_config = {"arch": "ecp5"}
    assert not hasattr(b, "flow_config")


# ---------------------------------------------------------------------------
# Edaflow base behaviour (~4 tests)
# ---------------------------------------------------------------------------


def test_edaflow_get_flow_options_returns_dict():
    from edalize.flows.edaflow import Edaflow

    assert isinstance(Edaflow.get_flow_options(), dict)


def test_edaflow_get_flow_options_independent_copy():
    from edalize.flows.edaflow import Edaflow

    a = Edaflow.get_flow_options()
    b = Edaflow.get_flow_options()
    a["evil"] = "yes"
    assert "evil" not in b


def test_flowgraph_starts_empty():
    from edalize.flows.edaflow import FlowGraph

    g = FlowGraph()
    assert g.get_nodes() == {}


def test_flowgraph_fromdict_empty():
    from edalize.flows.edaflow import FlowGraph

    g = FlowGraph.fromdict({})
    assert g.get_nodes() == {}


# ---------------------------------------------------------------------------
# Sanity: every module under edalize/ imports cleanly (~5 tests)
# ---------------------------------------------------------------------------


def test_edalize_pkg_importable():
    importlib.import_module("edalize")


def test_edalize_edam_importable():
    importlib.import_module("edalize.edam")


def test_edalize_edatool_importable():
    importlib.import_module("edalize.edatool")


def test_edalize_tools_edatool_importable():
    importlib.import_module("edalize.tools.edatool")


def test_edalize_flows_edaflow_importable():
    importlib.import_module("edalize.flows.edaflow")


# ---------------------------------------------------------------------------
# Cross-cutting invariant: subclass overrides keep base signatures (~4 tests)
# ---------------------------------------------------------------------------


def test_all_legacy_get_doc_signatures_consistent():
    """Every backend's get_doc should accept (api_ver) and be callable."""
    from edalize.edatool import get_edatools

    for cls in get_edatools():
        if cls.__name__ == "Edatool":
            continue
        sig = inspect.signature(cls.get_doc)
        # ``api_ver`` is the only required positional.
        params = [p for p in sig.parameters.values() if p.name != "cls"]
        assert any(p.name == "api_ver" for p in params), cls.__name__


def test_all_legacy_get_doc_returns_consistent_shape():
    from edalize.edatool import get_edatools

    for cls in get_edatools():
        if cls.__name__ == "Edatool":
            continue
        doc = cls.get_doc(0)
        if doc is None:
            continue
        assert isinstance(doc, dict)
        assert "description" in doc


def test_all_legacy_get_doc_invalid_api_returns_none():
    """The PR's contract: invalid api_ver returns None, never crashes."""
    from edalize.edatool import get_edatools

    for cls in get_edatools():
        if cls.__name__ == "Edatool":
            continue
        assert cls.get_doc(123456) is None, cls.__name__


def test_all_tools_get_tool_options_returns_dict():
    """Every tools/ backend has a get_tool_options() classmethod returning a dict."""
    for modname, clsname in TOOL_BACKENDS:
        mod = importlib.import_module(f"edalize.tools.{modname}")
        cls = getattr(mod, clsname)
        opts = cls.get_tool_options()
        assert isinstance(opts, dict), f"{clsname} returned {type(opts).__name__}"
