import os
import sys

sys.path.append(os.getenv("EFXPT_HOME") + "/bin")

import api_service.excp.design_excp as APIExcp
from api_service.design import DesignAPI

design = DesignAPI(False)

name = sys.argv[1]
part = sys.argv[2]
workdir = "."
isf_file = sys.argv[3]
design.create(name, part, workdir)
design.import_design(isf_file)
design.generate(enable_bitstream=False)
design.save_as(name + ".peri.xml")
