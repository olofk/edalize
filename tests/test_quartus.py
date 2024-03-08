import os
from .edalize_common import make_edalize_test

qsys_file = """<?xml version="1.0" encoding="UTF-8"?>
<system name="test">
 <component
   name="test"
   displayName="test"
   version="1.0"
   description=""
   tags=""
   categories="System"
   tool="{}"
   />
</system>
"""

qsys23_file = """<?xml version="1.0" ?>
<ipxact:design xmlns:altera="http://www.altera.com/XMLSchema/IPXact2014/extensions" xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2014">
  <ipxact:vendor>Altera Corporation</ipxact:vendor>
  <ipxact:library>sdm_mailbox</ipxact:library>
  <ipxact:name>sdm_mailbox</ipxact:name>
  <ipxact:version>1.0</ipxact:version>
  <ipxact:componentInstances></ipxact:componentInstances>
  <ipxact:vendorExtensions>
    <altera:catalog_card_info>
      <altera:version>1.0</altera:version>
      <altera:description></altera:description>
      <altera:tags></altera:tags>
      <altera:categories></altera:categories>
      <altera:tool>{}</altera:tool>
    </altera:catalog_card_info>
  </ipxact:vendorExtensions>
</ipxact:design>
"""

qsys_fill = {"Standard": "", "Pro": "QsysPro"}

test_sets = {
    "Standard": {
        "Quartus": [
            "ip-generate.cmd",
            "quartus_asm.cmd",
            "quartus_fit.cmd",
            "quartus_map.cmd",
            "quartus_sh.cmd",
            "quartus_sta.cmd",
        ],
        "DSE": [
            "ip-generate.cmd",
            "quartus_map.cmd",
            "quartus_sh.cmd",
            "quartus_dse.cmd",
        ],
    },
    "Pro": {
        "Quartus": [
            "qsys-generate.cmd",
            "quartus_asm.cmd",
            "quartus_fit.cmd",
            "quartus_syn.cmd",
            "quartus_sh.cmd",
            "quartus_sta.cmd",
        ],
        "DSE": [
            "qsys-generate.cmd",
            "quartus_syn.cmd",
            "quartus_sh.cmd",
            "quartus_dse.cmd",
        ],
    },
}


def test_quartus(make_edalize_test):
    tool_options = {
        "family": "Cyclone V",
        "device": "5CSXFC6D6F31C8ES",
        "quartus_options": ["some", "quartus_options"],
        "dse_options": ["some", "dse_options"],
    }

    # Test each edition of Quartus
    for edition in ["Standard", "Pro"]:
        for pnr in ["Quartus", "DSE"]:
            for qsys_format in [qsys_file, qsys23_file]:
                # Each edition and P&R tool has its own set of representative files
                if pnr == "DSE":
                    _tool_options = {**tool_options, "pnr": "dse"}
                else:
                    _tool_options = {**tool_options}

                # Ensure we test the edition we intend to, even if quartus_sh is
                # not present
                os.environ["FUSESOC_QUARTUS_EDITION"] = edition

                tf = make_edalize_test(
                    "quartus",
                    param_types=["vlogdefine", "vlogparam"],
                    tool_options=_tool_options,
                    ref_dir=edition,
                )

                # Each edition performs checks on the QSYS files present, so
                # provide a minimal example
                with open(os.path.join(tf.work_root, "qsys_file"), "w") as f:
                    f.write(qsys_format.format(qsys_fill[edition]))

                tf.backend.configure()
                tf.compare_files(["Makefile", tf.test_name + ".tcl"])

                tf.backend.build()
                tf.compare_files(test_sets[edition][pnr])
