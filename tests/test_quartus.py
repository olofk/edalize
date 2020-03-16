import pytest

qsys_file = """<?xml version="1.0" encoding="UTF-8"?>
<system name="test">
 <component
   name="test"
   displayName="test"
   version="1.0"
   description=""
   tags=""
   categories="System"
   {}
   />
</system>
"""

qsys_fill = {"Standard": "",
             "Pro"     : "tool=\"QsysPro\""}

test_sets = {"Standard": {"Quartus": ['ip-generate.cmd', 'quartus_asm.cmd', 'quartus_fit.cmd', 'quartus_map.cmd', 'quartus_sh.cmd', 'quartus_sta.cmd'],
                          "DSE"    : ['ip-generate.cmd', 'quartus_map.cmd', 'quartus_sh.cmd', 'quartus_dse.cmd']},
             "Pro"     : {"Quartus": ['qsys-generate.cmd', 'quartus_asm.cmd', 'quartus_fit.cmd', 'quartus_syn.cmd', 'quartus_sh.cmd', 'quartus_sta.cmd'],
                          "DSE"    : ['qsys-generate.cmd', 'quartus_syn.cmd', 'quartus_sh.cmd', 'quartus_dse.cmd']}}

def test_quartus():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_quartus_0'
    tool         = 'quartus'
    tool_options = {
        'family'          : 'Cyclone V',
        'device'          : '5CSXFC6D6F31C8ES',
        'quartus_options' : ['some', 'quartus_options'],
    }

    # Test each edition of Quartus
    for edition in ["Standard", "Pro"]:
        for pnr in ["Quartus", "DSE"]:
            # Each edition and P&R tool has its own set of representative files
            ref_dir       = os.path.join(tests_dir, __name__, edition)

            if pnr == "DSE":
                _tool_options = {**tool_options, "pnr": "dse"}
            else:
                _tool_options = {**tool_options}

            # Ensure we test the edition we intend to, even if quartus_sh is present
            os.environ["FUSESOC_QUARTUS_EDITION"] = edition
            (backend, work_root) = setup_backend(paramtypes, name, tool, _tool_options)

            # Each edition performs checks on the QSYS files present, so provide
            # a minimal example
            with open(os.path.join(work_root, "qsys_file"), 'w') as f:
                f.write(qsys_file.format(qsys_fill[edition]))

            backend.configure()

            compare_files(ref_dir, work_root, ['Makefile',
                                               name+'.tcl'])

            backend.build()
            compare_files(ref_dir, work_root, test_sets[edition][pnr])
