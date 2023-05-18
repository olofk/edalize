import pytest


def test_empty_edam():
    import tempfile
    from edalize.edatool import get_edatool

    (h, edam_file) = tempfile.mkstemp()

    with pytest.raises(TypeError):
        backend = get_edatool("icarus")(edam=None)


def test_incomplete_edam():
    from edalize.edatool import get_edatool

    with pytest.raises(RuntimeError) as excinfo:
        backend = get_edatool("icarus")(edam={"version": "0.1.2"})
    assert "Missing required parameter 'name'" in str(excinfo.value)

    backend = get_edatool("icarus")(edam={"version": "0.1.2", "name": "corename"})


def test_edam_files():
    from edalize.edatool import get_edatool

    files = [
        {"name": "plain_file"},
        {"name": "subdir/plain_include_file", "is_include_file": True},
        {
            "name": "file_with_args",
            "file_type": "verilogSource",
            "logical_name": "libx",
        },
        {
            "name": "include_file_with_args",
            "is_include_file": True,
            "file_type": "verilogSource",
            "logical_name": "libx",
        },
    ]
    edam = {"files": files, "name": "test_edam_files"}

    backend = get_edatool("icarus")(edam=edam)
    (parsed_files, incdirs) = backend._get_fileset_files()

    assert len(parsed_files) == 2
    assert parsed_files[0].name == "plain_file"
    assert parsed_files[0].file_type == ""
    assert parsed_files[0].logical_name == ""
    assert parsed_files[1].name == "file_with_args"
    assert parsed_files[1].file_type == "verilogSource"
    assert parsed_files[1].logical_name == "libx"

    assert incdirs == ["subdir", "."]


def test_verilog_include_file_with_include_path():
    from edalize.edatool import get_edatool

    files = [
        {
            "name": "some_dir/some_file",
            "file_type": "verilogSource",
            "is_include_file": True,
            "include_path": "some_dir",
        }
    ]
    edam = {"files": files, "name": "test_edam_files"}

    backend = get_edatool("icarus")(edam=edam)
    (parsed_files, incdirs) = backend._get_fileset_files()

    assert len(parsed_files) == 0
    assert incdirs == ["some_dir"]


def test_verilog_include_file_with_partial_include_path():
    from edalize.edatool import get_edatool

    files = [
        {
            "name": "../some_dir/some_subdir/some_file",
            "file_type": "verilogSource",
            "is_include_file": True,
            "include_path": "../some_dir",
        }
    ]
    edam = {"files": files, "name": "test_edam_files"}

    backend = get_edatool("icarus")(edam=edam)
    (parsed_files, incdirs) = backend._get_fileset_files()

    assert len(parsed_files) == 0
    assert incdirs == ["../some_dir"]


def test_edam_hook_failing(tmpdir):
    import os.path
    from edalize.edatool import get_edatool

    tests_dir = os.path.dirname(__file__)
    ref_dir = os.path.join(tests_dir, __name__)

    script = "exit_1_script"
    hooks = {
        "pre_build": [{"cmd": ["sh", os.path.join(ref_dir, script)], "name": script}]
    }

    work_root = str(tmpdir)
    edam = {"hooks": hooks, "name": script}

    backend = get_edatool("icarus")(edam=edam, work_root=work_root)
    exc_str_exp = (
        r"pre_build script 'exit_1_script': "
        r"\['sh', '.+/exit_1_script'\] exited with error code "
    )
    with pytest.raises(RuntimeError, match=exc_str_exp):
        backend.build_pre()


def test_edam_multiple_hooks(tmpdir):
    """Test if more than one hook gets successfully executed."""

    import os.path
    from edalize.edatool import get_edatool

    hooks = {
        "pre_build": [
            {
                "cmd": ["touch", "hook_1_executed.txt"],
                "name": "hook_1",
            },
            {
                "cmd": ["touch", "hook_2_executed.txt"],
                "name": "hook_2",
            },
        ]
    }

    work_root = str(tmpdir)
    edam = {"hooks": hooks, "name": "test_edam_multiple_hooks"}

    assert not os.path.exists(os.path.join(work_root, "hook_1_executed.txt"))
    assert not os.path.exists(os.path.join(work_root, "hook_2_executed.txt"))

    backend = get_edatool("icarus")(edam=edam, work_root=work_root)
    backend.build_pre()

    assert os.path.exists(os.path.join(work_root, "hook_1_executed.txt"))
    assert os.path.exists(os.path.join(work_root, "hook_2_executed.txt"))
