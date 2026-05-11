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

# ``NotRequired`` only joined :mod:`typing` in Python 3.11.  Split the import
# so mypy can follow the version branch statically.
if sys.version_info >= (3, 11):
    from typing import NotRequired, TypedDict
else:
    from typing_extensions import NotRequired, TypedDict


# ---------------------------------------------------------------------------
# Leaf-level structures
# ---------------------------------------------------------------------------


class File(TypedDict, total=False):
    """A single source file entry inside ``edam["files"]``."""

    name: str
    file_type: str
    is_include_file: bool
    include_path: str
    logical_name: str
    core: str
    # Backend-specific tags that gate inclusion in a particular flow.
    tags: List[str]
    # Per-file Verilog defines merged on top of the global ones.
    define: Dict[str, Any]
    # Free-form version label used by a few vendor backends.
    version: str


ParamType = Literal[
    "plusarg",
    "vlogparam",
    "vlogdefine",
    "generic",
    "cmdlinearg",
]
"""How a parameter is delivered to the underlying tool."""


DataType = Literal["bool", "file", "int", "str"]
"""The Python datatype of a parameter's value."""


class Parameter(TypedDict, total=False):
    """A single entry inside ``edam["parameters"]``."""

    datatype: DataType
    default: Union[bool, int, str]
    description: str
    paramtype: ParamType


class HookScript(TypedDict, total=False):
    """A single hook script entry."""

    name: str
    cmd: List[str]
    env: Dict[str, str]


HookName = Literal["pre_build", "post_build", "pre_run", "post_run"]


class Hooks(TypedDict, total=False):
    """The ``edam["hooks"]`` dictionary."""

    pre_build: List[HookScript]
    post_build: List[HookScript]
    pre_run: List[HookScript]
    post_run: List[HookScript]


class VpiModule(TypedDict, total=False):
    """A single VPI module entry inside ``edam["vpi"]``."""

    name: str
    src_files: List[str]
    include_dirs: List[str]
    libs: List[str]


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

    Only ``name`` is strictly required by ``Edatool.__init__``; everything else
    has a sensible default of ``[]`` / ``{}``. We mark them all as
    ``NotRequired`` so user code can build EDAMs incrementally.
    """

    # Mandatory
    name: str

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


# ---------------------------------------------------------------------------
# Convenience aliases (used heavily across backends)
# ---------------------------------------------------------------------------

# The shape returned by ``argparse`` after CLI parsing — keys are parameter
# names, values are whatever ``argparse`` produced (str / int / bool / list).
RunArgs = Dict[str, Any]

# The dict produced by ``Edatool.get_doc(0)``.
ToolDoc = Dict[str, Any]


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
    "ToolOptions",
    "VpiModule",
]
