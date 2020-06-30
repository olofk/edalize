import pytest
from edalize_common import make_edalize_test


def test_vivado(make_edalize_test):
    tf = make_edalize_test('vivado',
                           param_types=['generic', 'vlogdefine', 'vlogparam'],
                           tool_options={'part': 'xc7a35tcsg324-1'})

    tf.backend.configure()
    tf.compare_files(['Makefile',
                      tf.test_name + '.tcl',
                      tf.test_name + '_synth.tcl',
                      tf.test_name + '_run.tcl',
                      tf.test_name + '_pgm.tcl'])

    tf.backend.build()
    tf.compare_files(['vivado.cmd'])


@pytest.mark.parametrize("params", [("minimal", "vivado"), ("yosys", "yosys")])
def test_vivado_minimal(params, tmpdir):
    import os

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
    work_root = str(tmpdir)

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
