import pytest

def test_vivado():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['generic', 'vlogdefine', 'vlogparam']
    name         = 'test_vivado_0'
    tool         = 'vivado'
    tool_options = {
        'part' : 'xc7a35tcsg324-1',
    }

    (backend, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure()

    compare_files(ref_dir, work_root, [
        'Makefile',
        name+'.tcl',
        name+'_synth.tcl',
        name+'_run.tcl',
        name+'_pgm.tcl',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'vivado.cmd',
    ])


@pytest.mark.parametrize("params", [("minimal", "vivado"), ("yosys", "yosys")])
def test_vivado_minimal(params):
    import os
    import shutil
    import tempfile

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    test_name, synth_tool = params

    ref_dir      = os.path.join(tests_dir, __name__, test_name)
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'vivado'
    tool_options = {
        'part' : 'xc7a35tcsg324-1',
        'synth': synth_tool,
    }
    name = 'test_vivado_{}_0'.format(test_name)
    work_root = tempfile.mkdtemp(prefix=tool+'_')

    edam = {'name'         : name,
            'tool_options' : {'vivado' : tool_options}
    }

    backend = get_edatool(tool)(edam=edam, work_root=work_root)
    backend.configure()

    config_file_list = [
        'Makefile',
        name+'.tcl',
        name+'_run.tcl',
        name+'_pgm.tcl',
    ]

    if synth_tool == "yosys":
        config_file_list.append(name+'.mk')
        config_file_list.append('yosys.tcl')
    else:
        config_file_list.append(name+'_synth.tcl')

    compare_files(ref_dir, work_root, config_file_list)

    build_file_list = ['vivado.cmd']

    if synth_tool == "yosys":
        build_file_list.append('yosys.cmd')

    backend.build()
    compare_files(ref_dir, work_root, build_file_list)
