import os
import pytest
from edalize_common import make_edalize_test


@pytest.mark.parametrize("params", [("minimal", "vpr")])
def test_vpr(params, tmpdir):
    import os
    import edalize
    from edalize_common import compare_files, tests_dir

    test_name = "vpr"
    ref_dir = os.path.join(tests_dir, __name__, test_name)
    os.environ["PATH"] = (
        os.path.join(tests_dir, "mock_commands") + ":" + os.environ["PATH"]
    )
    tool = "vpr"
    name = "test_vpr_{}_0".format(test_name)
    work_root = str(tmpdir)

    edam = {
        "name": name,
        "flow_options": {
            "arch": "xilinx",
            "arch_xml": "/tmp/k6_N10_mem32K_40nm.xml",
            "vpr_options": [],
        },
    }

    vpr_flow = edalize.get_flow("vpr")
    vpr_backend = vpr_flow(edam=edam, work_root=work_root)
    vpr_backend.configure()
    config_file_list = [
        "Makefile",
    ]
    compare_files(ref_dir, work_root, config_file_list)
