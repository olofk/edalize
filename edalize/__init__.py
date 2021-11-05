# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from importlib import import_module
from os.path import dirname
from pkgutil import walk_packages

NON_TOOL_PACKAGES = [
    "vunit_hooks",
    "reporting",
    "ise_reporting",
    "vivado_reporting",
    "quartus_reporting",
]


def get_edatool(name):
    return getattr(import_module("{}.{}".format(__name__, name)), name.capitalize())


def walk_tool_packages():
    for _, pkg_name, _ in walk_packages([dirname(__file__)]):
        if not pkg_name in NON_TOOL_PACKAGES:
            yield pkg_name


def get_edatools():
    return [get_edatool(pkg) for pkg in walk_tool_packages()]
