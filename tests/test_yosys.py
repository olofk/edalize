import pytest
from edalize_common import make_edalize_test

def test_yosys_tech(make_edalize_test):
    tf = make_edalize_test(
        'yosys',
        param_types = ['vlogdefine', 'vlogparam'],
        tool_options = {
            'tech_lib': '/some/path/to/your/tech.lib',
            'arch': 'stdcell',
            'output_format': 'verilog'
        }
    )
    tf.backend.configure()
    tf.compare_files(['Makefile', tf.test_name + '.tcl'])

    tf.backend.build()
    tf.compare_files(['yosys.cmd'])

def test_yosys_illegal_tech(make_edalize_test):
    tf = make_edalize_test(
        'yosys',
        tool_options = {
            'arch': 'stdcell'
        }
    )
    with pytest.raises(RuntimeError) as e:
        tf.backend.configure()  
    assert "Yosys arch is set to 'stdcell' but no 'tech_lib' has been defined" == str(e.value)
