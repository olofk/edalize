# Auto generated by Edalize

from vunit.vhdl_standard import VHDL

def load_module_from_file(name, python_file):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, python_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_runner_hooks(python_file = r''):
    if len(python_file) > 0:
        return load_module_from_file('vunit_runner_hooks', python_file)
    else:
        return __import__('edalize.vunit_hooks', fromlist=['vunit_hooks'])

runner = load_runner_hooks().VUnitRunner()

# Override this hook to allow custom creation configuration of the VUnit instance:
vu = runner.create()


lib = vu.add_library("vunit_test_runner_lib")
lib.add_source_files("sv_file.sv")
lib.add_source_files("vlog_file.v")
lib.add_source_files("vlog05_file.v")
lib.add_source_files("vhdl_file.vhd")
lib.add_source_files("vhdl2008_file", vhdl_standard=VHDL.standard("2008"))
# Override this hook to customize the library, e.g. compile-flags etc.
# This allows full access to vunit.ui.Library interface:
runner.handle_library("vunit_test_runner_lib", lib)

lib = vu.add_library("libx")
lib.add_source_files("vhdl_lfile")
# Override this hook to customize the library, e.g. compile-flags etc.
# This allows full access to vunit.ui.Library interface:
runner.handle_library("libx", lib)


# override this hook to perform final customization and parametrization of VUnit, custom invokation, etc.
runner.main(vu)
