# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.flows.vpr import Vpr

logger = logging.getLogger(__name__)


class Vpr(Edatool):
    """
    VPR tool Backend

    The VPR backend performs Packing, Placement, Routing & Timing Analysis.
    VPR is an open source academic CAD tool designed for the exploration of new FPGA architectures and CAD algorithms, at the packing, placement and routing phases of the CAD flow

    """

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The VPR backend performs Packing, Placement, Routing & Timing Analysis.",
                "members": [
                    {
                        "name": "arch_xml",
                        "type": "String",
                        "desc": "Path to target architecture.",
                    },
                    {
                        "name": "vpr_options",
                        "type": "String",
                        "desc": "Additional options for VPR.",
                    },
                ],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        edam["flow_options"] = edam["tool_options"]["vpr"]
        self.vpr = VPR(edam, work_root, verbose)

    def configure_main(self):
        self.vpr.configure()

    def build_pre(self):
        pass

    def build_post(self):
        pass
