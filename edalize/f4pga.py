# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from edalize.edatool import Edatool
from edalize.flows.f4pga import F4pga as F4pga_underlying


class F4pga(Edatool):
    """Edalize front-end F4PGA interface"""

    def __init__(self, edam=None, work_root=None, eda_api=None, verbose=True):
        super().__init__(edam, work_root, eda_api, verbose)
        self.f4pga = F4pga_underlying(edam, work_root, verbose)
