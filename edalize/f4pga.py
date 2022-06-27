# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.edatool import Edatool
from edalize.flows.f4pga import F4pga as F4PGA_Flow

class F4pga(Edatool):
    """
    F4PGA backend (Edatool portion)

    Calls the tools that F4PGA uses with the specified options
    """

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description" : "F4PGA Edatool backend (Yosys and VPR)"
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        edam["flow_options"] = edam["tool_options"]["f4pga"]
        self.f4pga = F4PGA_Flow(edam, work_root, verbose)

    def configure_main(self):
        self.f4pga.configure()

    def run_main(self):
        self.f4pga.run(args=[])