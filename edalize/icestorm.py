# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path

from edalize.edatool import Edatool
from edalize.nextpnr import Nextpnr
from edalize.yosys import Yosys
from edalize.flows.icestorm import Icestorm as Icestorm2


class Icestorm(Edatool):

    argtypes = ["vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            options = {
                "members": [
                    {
                        "name": "pnr",
                        "type": "String",
                        "desc": "Select Place & Route tool. Legal values are *arachne* for Arachne-PNR, *next* for nextpnr or *none* to only perform synthesis. Default is next",
                    },
                ],
                "lists": [
                    {
                        "name": "arachne_pnr_options",
                        "type": "String",
                        "desc": "Additional options for Arachnhe PNR",
                    },
                    {
                        "name": "frontends",
                        "type": "String",
                        "desc": "fixme",
                    },
                ],
            }
            Edatool._extend_options(options, Yosys)
            Edatool._extend_options(options, Nextpnr)

            return {
                "description": "Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and arachne-pnr or nextpnr for Place & Route",
                "members": options["members"],
                "lists": options["lists"],
            }

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        _tool_opts = edam["tool_options"]["icestorm"]

        edam["flow_options"] = edam["tool_options"]["icestorm"]

        self.icestorm = Icestorm2(edam, work_root, verbose)

    def configure_main(self):
        self.icestorm.configure()

    def build_pre(self):
        pass

    def build_main(self):
        self.icestorm.build()

    def build_post(self):
        pass
