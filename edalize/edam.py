# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

"""Typed structures for the EDAM (EDA-API Metadata) dictionary.

EDAM is the contract between FuseSoC (the producer) and Edalize (the consumer).
Modelling it as :class:`TypedDict` lets static type-checkers verify backends
without changing any runtime behaviour — the dicts still serialise to plain
JSON / YAML.

The types are intentionally permissive (``total=False``) because the EDAM
schema has grown organically and many fields are optional or tool-specific.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Literal, Union

# ``NotRequired`` / ``Required`` joined :mod:`typing` in Python 3.11.  Split
# the import so mypy can follow the version branch statically.
if sys.version_info >= (3, 11):
    from typing import NotRequired, Required, TypedDict
else:
    from typing_extensions import NotRequired, Required, TypedDict


# ---------------------------------------------------------------------------
# Leaf-level structures
# ---------------------------------------------------------------------------


class File(TypedDict):
    """A single source file entry inside ``edam["files"]``.

    ``name`` is required because FuseSoC always emits it and every backend
    indexes ``f["name"]`` directly. All other keys are optional.
    """

    name: Required[str]
    file_type: NotRequired[str]
    is_include_file: NotRequired[bool]
    include_path: NotRequired[str]
    logical_name: NotRequired[str]
    core: NotRequired[str]
    # Backend-specific tags that gate inclusion in a particular flow.
    tags: NotRequired[List[str]]
    # Per-file Verilog defines merged on top of the global ones.
    define: NotRequired[Dict[str, Any]]
    # Free-form version label used by a few vendor backends.
    version: NotRequired[str]


ParamType = Literal[
    "plusarg",
    "vlogparam",
    "vlogdefine",
    "generic",
    "cmdlinearg",
]
"""How a parameter is delivered to the underlying tool."""


DataType = Literal["bool", "file", "int", "real", "str"]
"""The Python datatype of a parameter's value.

Must mirror FuseSoC's CAPI2 schema (``fusesoc/capi2/json_schema.py``).
"""


class Parameter(TypedDict):
    """A single entry inside ``edam["parameters"]``.

    ``datatype`` and ``paramtype`` are required: FuseSoC's CAPI2 schema
    rejects parameters missing them, and ``parse_args`` / ``_apply_parameters``
    index both directly. ``default`` and ``description`` are optional.
    """

    datatype: Required[DataType]
    paramtype: Required[ParamType]
    default: NotRequired[Union[bool, int, float, str]]
    description: NotRequired[str]


class HookScript(TypedDict):
    """A single hook script entry.

    ``Edatool._run_scripts`` and ``Edaflow.add_scripts`` index ``name``
    and ``cmd`` unconditionally, so they are required; ``env`` is
    optional.
    """

    name: Required[str]
    cmd: Required[List[str]]
    env: NotRequired[Dict[str, str]]


HookName = Literal["pre_build", "post_build", "pre_run", "post_run"]


class Hooks(TypedDict, total=False):
    """The ``edam["hooks"]`` dictionary."""

    pre_build: List[HookScript]
    post_build: List[HookScript]
    pre_run: List[HookScript]
    post_run: List[HookScript]


class VpiModule(TypedDict):
    """A single VPI module entry inside ``edam["vpi"]``.

    FuseSoC always emits all four keys when it emits a VPI entry, and
    multiple backends index them directly, so all are required.
    """

    name: Required[str]
    src_files: Required[List[str]]
    include_dirs: Required[List[str]]
    libs: Required[List[str]]


# ---------------------------------------------------------------------------
# Tool options
# ---------------------------------------------------------------------------

# Tool options vary wildly per backend, so we model the outer dict (keyed by
# tool name) but not the inner contents. Per-backend modules can declare their
# own ``TypedDict`` and narrow when accessing ``self.tool_options``.
ToolOptions = Dict[str, Dict[str, Any]]


# ---------------------------------------------------------------------------
# Top-level EDAM
# ---------------------------------------------------------------------------


class Edam(TypedDict, total=False):
    """The top-level EDAM dictionary handed to every backend.

    ``name`` is the only key ``Edatool.__init__`` indexes unconditionally,
    so we mark it ``Required``.  Everything else has a sensible
    ``[]`` / ``{}`` default and is ``NotRequired``.
    """

    # Mandatory — ``Edatool.__init__`` does ``edam["name"]`` directly.
    name: Required[str]

    # Sources & build inputs
    files: List[File]
    toplevel: Union[str, List[str]]
    vpi: List[VpiModule]

    # Configuration
    tool_options: ToolOptions
    parameters: Dict[str, Parameter]
    hooks: Hooks

    # Used only by the ``flows`` API
    flow_options: Dict[str, Any]
    flow: Dict[str, Any]

    # Set by FuseSoC's edalizer (see fusesoc.edalizer):
    #   * EDAM schema version (currently "0.2.1")
    #   * per-core metadata bundle
    #   * resolved per-core dependency map
    #   * list of filter names to apply before tool dispatch
    version: str
    cores: Dict[str, Any]
    dependencies: Dict[str, List[str]]
    filters: List[str]


# ---------------------------------------------------------------------------
# Convenience aliases (used heavily across backends)
# ---------------------------------------------------------------------------

# The shape returned by ``argparse`` after CLI parsing — keys are parameter
# names, values are whatever ``argparse`` produced (str / int / bool / list).
RunArgs = Dict[str, Any]


class ToolDocEntry(TypedDict):
    """A single ``members`` / ``lists`` / ``dicts`` row inside a tool doc.

    ``_class_doc()`` indexes all three keys unconditionally.
    """

    name: Required[str]
    type: Required[str]
    desc: Required[str]


class ToolDoc(TypedDict):
    """The dict produced by ``Edatool.get_doc(0)``.

    ``description`` is required because every consumer of ``ToolDoc``
    indexes it directly; the three group lists are optional, populated
    only when the backend declares options of that shape.
    """

    description: Required[str]
    members: NotRequired[List[ToolDocEntry]]
    lists: NotRequired[List[ToolDocEntry]]
    dicts: NotRequired[List[ToolDocEntry]]


__all__ = [
    "DataType",
    "Edam",
    "File",
    "HookName",
    "HookScript",
    "Hooks",
    "Parameter",
    "ParamType",
    "RunArgs",
    "ToolDoc",
    "ToolDocEntry",
    "ToolOptions",
    "VpiModule",
]
