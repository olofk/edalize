import pytest
import os.path
from unittest.mock import patch, MagicMock
from .edalize_common import make_edalize_test
import edalize.edatool


def test_vunit_codegen(make_edalize_test):
    tf = make_edalize_test("vunit", param_types=["cmdlinearg"])
    tf.backend.configure()
    tf.compare_files(["run.py"])


def test_vunit_hooks(tmpdir):
    from .edalize_common import tests_dir

    import subprocess
    import sys
    import importlib.util
    from unittest import mock
    from edalize.edatool import get_edatool

    sys.path = [os.path.join(tests_dir, "test_vunit", "vunit_mock")] + sys.path

    ref_dir = os.path.join(tests_dir, "test_vunit", "minimal")
    tool = "vunit"
    name = "test_" + tool + "_minimal_0"
    work_root = str(tmpdir)

    files = [
        {
            "name": os.path.join(ref_dir, "vunit_runner_test.py"),
            "file_type": "pythonSource-3.7",
        },
        {
            "name": os.path.join(ref_dir, "tb_minimal.vhd"),
            "file_type": "vhdlSource-2008",
            "logical_name": "libx",
        },
    ]

    edam = {"name": name, "files": files, "toplevel": "top"}

    backend = get_edatool(tool)(edam=edam, work_root=work_root)

    original_impl = edalize.edatool.run

    def subprocess_intercept(args, **kwargs):
        if len(args) > 1 and args[1].endswith("run.py"):
            import sys

            with patch.object(sys, "argv", args):
                spec = importlib.util.spec_from_file_location("__main__", args[1])
                runner_script = importlib.util.module_from_spec(spec)

                returncode = spec.loader.exec_module(runner_script)
                return subprocess.CompletedProcess(args, returncode)
        else:
            return original_impl(args, **kwargs)

    with mock.patch("edalize.edatool.run", new=subprocess_intercept):
        backend.configure()

        with mock.patch("edalize.vunit_hooks.VUnitRunner") as hooks_constructor:
            hooks = MagicMock()
            vu_library = MagicMock()
            vu_mock = MagicMock()
            hooks_constructor.return_value = hooks
            hooks.create.return_value = vu_mock
            vu_mock.add_library.return_value = vu_library

            backend.build()

            hooks_constructor.assert_called_once_with()
            hooks.create.assert_called_once_with()

            vu_mock.add_library.assert_called_with("libx")
            hooks.create.assert_called_once_with()
            hooks.handle_library.assert_called_with("libx", vu_library)
            hooks.main.assert_called_with(vu_mock)

        with mock.patch("edalize.vunit_hooks.VUnitRunner") as hooks_constructor:
            hooks = MagicMock()
            vu_library = MagicMock()
            vu_mock = MagicMock()
            hooks_constructor.return_value = hooks
            hooks.create.return_value = vu_mock
            vu_mock.add_library.return_value = vu_library

            backend.run()

            hooks_constructor.assert_called_once_with()
            hooks.create.assert_called_once_with()
            vu_mock.add_library.assert_called_with("libx")
            hooks.create.assert_called_once_with()
            hooks.handle_library.assert_called_with("libx", vu_library)
            hooks.main.assert_called_with(vu_mock)


@pytest.mark.parametrize("with_source_files", [True, False])
def test_vunit_empty_cores(tmp_path, monkeypatch, with_source_files):
    import runpy
    import sys
    from types import ModuleType

    from edalize.edatool import get_edatool

    sources = {
        "design.vhd": MagicMock(),
        "dependency.vhd": MagicMock(),
    }
    files = (
        [
            {"name": name, "file_type": "vhdlSource", "core": core}
            for name, core in (
                ("design.vhd", "design"),
                ("dependency.vhd", "dependency"),
            )
        ]
        if with_source_files
        else []
    )
    edam = {
        "name": "empty_cores",
        "toplevel": "top",
        "files": files,
        "dependencies": {
            "empty": [],
            "dependency": [],
            "design": ["dependency", "empty"],
        },
    }
    backend = get_edatool("vunit")(edam=edam, work_root=str(tmp_path))
    backend.configure()

    hooks = MagicMock()
    vu = hooks.create.return_value
    vu.add_library.return_value.add_source_file.side_effect = lambda name: sources[name]
    hooks_module = ModuleType("edalize.vunit_hooks")
    hooks_module.VUnitRunner = MagicMock(return_value=hooks)
    monkeypatch.setitem(sys.modules, "edalize.vunit_hooks", hooks_module)

    result = runpy.run_path(str(tmp_path / "run.py"))

    assert result["core_files"]["empty"] == []
    if with_source_files:
        sources["design.vhd"].add_dependency_on.assert_any_call(
            [sources["dependency.vhd"]]
        )
        sources["dependency.vhd"].add_dependency_on.assert_not_called()
    else:
        vu.add_library.assert_not_called()
    hooks.main.assert_called_once_with(vu)


if __name__ == "__main__":
    from os.path import dirname
    import sys

    sys.path.append(dirname(dirname(__file__)))
    pytest.main(args=[__file__])
