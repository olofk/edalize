import os

from edalize.tools.edatool import Edatool


def test_update_config_file_appends_and_dedup(tmp_path):
    work_root = str(tmp_path)

    tool = Edatool()
    tool.work_root = work_root

    fname = "cfg.txt"
    fpath = os.path.join(work_root, fname)

    with open(fpath, "w") as f:
        f.write("initial\n")

    tool.update_config_file(fname, "more\n")

    with open(fpath, "r") as f:
        data = f.read()
    assert data == "initial\nmore\n"

    # If already exists, don't append again
    tool.update_config_file(fname, "more\n")
    with open(fpath, "r") as f:
        data2 = f.read()
    assert data2 == data
