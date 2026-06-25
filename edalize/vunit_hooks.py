# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

"""
This module exports :class:`VUnitHooks` which can be used to implement advanced VUnit test cases.
"""

from __future__ import annotations

from vunit.ui import Library
from vunit import VUnit


class VUnitHooks(object):
    """
    Derive the :class:`VUnitRunner` instance from this class and override its member functions if necessary.
    """

    def __init__(self) -> None:
        pass

    def create(self) -> VUnit:
        """
        Override this function to specify custom instantiation of VUnit.
        """
        return VUnit.from_argv()

    def handle_library(self, logical_name: str, vu_lib: Library) -> None:
        """
        Override this to customize each library, e.g. with additional simulator options.
        """
        pass

    def main(self, vu: VUnit) -> None:
        """
        Override this for final parametrization of the :class:`~vunit.ui.VUnit` instance, or for custom invocation of VUnit.
        """
        vu.main()


class VUnitRunner(VUnitHooks):
    """
    The default runner which will be used if no :file:`vunit_runner.py` is specified.
    """

    pass
