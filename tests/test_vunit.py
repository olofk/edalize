import pytest
import os.path
from unittest.mock import patch, MagicMock
from edalize_common import make_edalize_test
import edalize.edatool


def test_vunit_codegen(make_edalize_test):
    tf = make_edalize_test('vunit', param_types=['cmdlinearg'])
    tf.backend.configure()
    tf.compare_files(['run.py'])


def test_vunit_hooks(tmpdir):
    from edalize_common import tests_dir

    import subprocess
    import sys
    import importlib.util
    from unittest import mock
    from edalize import get_edatool

    sys.path = [os.path.join(tests_dir, __name__, 'vunit_mock')] + sys.path

    ref_dir = os.path.join(tests_dir, __name__, 'minimal')
    tool = 'vunit'
    name = 'test_' + tool + '_minimal_0'
    work_root = str(tmpdir)

    files = [{'name' : os.path.join(ref_dir, 'vunit_runner_test.py'),
              'file_type' : 'pythonSource-3.7'},
             {'name' : os.path.join(ref_dir, 'tb_minimal.vhd'),
              'file_type' : 'vhdlSource-2008',
              'logical_name' : 'libx'}]

    edam = {'name'     : name,
            'files'    : files,
            'toplevel' : 'top'}

    backend = get_edatool(tool)(edam=edam, work_root=work_root)

    original_impl = edalize.edatool.run

    def subprocess_intercept(args, **kwargs):
        if len(args) > 1 and args[1].endswith('run.py'):
            import sys
            with patch.object(sys, 'argv', args):
                spec = importlib.util.spec_from_file_location("__main__", args[1])
                runner_script = importlib.util.module_from_spec(spec)

                returncode = spec.loader.exec_module(runner_script)
                return subprocess.CompletedProcess(args, returncode)
        else:
            return original_impl(args, **kwargs)

    with mock.patch('edalize.edatool.run', new=subprocess_intercept):
        backend.configure()

        with mock.patch('edalize.vunit_hooks.VUnitRunner') as hooks_constructor:
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
            hooks.handle_library.assert_called_with('libx', vu_library)
            hooks.main.assert_called_with(vu_mock)

        with mock.patch('edalize.vunit_hooks.VUnitRunner') as hooks_constructor:
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
            hooks.handle_library.assert_called_with('libx', vu_library)
            hooks.main.assert_called_with(vu_mock)


if __name__ == '__main__':
    from os.path import dirname
    import sys
    sys.path.append(dirname(dirname(__file__)))
    pytest.main(args=[__file__])
