# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.edatool import Edatool
from edalize.flows.f4pga import F4pga as F4pga_underlying


class F4pga(Edatool):
    """Edalize front-end F4PGA interface"""

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "F4PGA is an open-source flow for generating bitstreams from verilog/systemverilog code using Yosys and VPR/NextPNR. Currently only supports Xilinx 7-series boards with support for more coming in the future.",
                "members": [
                    {
                        "name": "device",
                        "type": "str",
                        "desc": "(Required) The device type identifier. Example: 'artix7'",
                    },
                    {
                        "name": "part",
                        "type": "str",
                        "desc": "(Required) The FPGA part specifier. Example: 'xc7a35tcpg236-1'",
                    },
                    {
                        "name": "chip",
                        "type": "str",
                        "desc": "(Required) The FPGA chip specifier used by F4PGA. Example: 'xc7a50t_test'",
                    },
                    {
                        "name": "arch",
                        "type": "str",
                        "desc": "(Optional) The architecture specifier. Currently defaults to xilinx and is thus optional.",
                    },
                    {
                        "name": "pnr",
                        "type": "str",
                        "desc": "(Optional) The name of the place and route tool to use. Defaults to VPR and is thus optional.",
                    },
                ],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        self.f4pga = F4pga_underlying(edam, work_root, verbose)

    def configure_main(self):
        self.f4pga.configure()

    def run_main(self):
        pass
