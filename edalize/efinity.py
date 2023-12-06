# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.flows.efinity import Efinity as Efinity_underlying

logger = logging.getLogger(__name__)


class Efinity(Edatool):
    """
    Efinity Backend.

    A core (usually the system core) can add the following files:

    * Standard design sources
    * Constraints
    """

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The Efinity backend executes Efinity to build systems and program the FPGA",
                "members": [
                    {
                        "name": "family",
                        "type": "String",
                        "desc": "Accepted is Trion and Titanium (default)",
                    },
                    {
                        "name": "part",
                        "type": "String",
                        "desc": "FPGA part number (e.g. Ti180M484)",
                    },
                    {
                        "name": "timing",
                        "type": "String",
                        "desc": "Speed grade (e.g. C4)",
                    },
                ],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        # edam["flow_options"] = edam["tool_options"]["efinity"]
        self.efinity = Efinity_underlying(edam, work_root, verbose)

    def configure_main(self):
        self.efinity.configure()

    def build_main(self):
        """
        Synthesize and place
        """
        logger.info("Building")
        args = []
        self._run_tool("make", args)
