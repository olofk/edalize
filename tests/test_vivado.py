import pytest
from .edalize_common import get_flow, make_edalize_test


def test_vivado(make_edalize_test):
    tf = make_edalize_test(
        "vivado",
        param_types=["generic", "vlogdefine", "vlogparam"],
        tool_options={"part": "xc7a35tcsg324-1"},
    )
    tf.backend.configure()
    tf.compare_files(
        [
            "Makefile",
            tf.test_name + ".tcl",
            tf.test_name + "_synth.tcl",
            tf.test_name + "_run.tcl",
            tf.test_name + "_pgm.tcl",
        ]
    )

    tf.backend.build()
    tf.compare_files(["vivado.cmd"])


@pytest.mark.parametrize("params", [("minimal", "vivado"), ("yosys", "yosys")])
def test_vivado_minimal(params, tmpdir, make_edalize_test):
    import os

    import edalize
    from .edalize_common import compare_files, tests_dir

    test_name, synth_tool = params

    os.environ["PATH"] = (
        os.path.join(tests_dir, "mock_commands") + ":" + os.environ["PATH"]
    )
    tool = "vivado"
    tool_options = {
        "part": "xc7a35tcsg324-1",
    }
    name = "test_vivado_{}_0".format(test_name)
    work_root = str(tmpdir)
    edam = {
        "name": name,
        "flow_options": {"synth": synth_tool, "part": "xc7a35tcsg324-1"},
    }
    vivado_flow = get_flow("vivado")
    vivado_backend = vivado_flow(edam=edam, work_root=work_root)
    vivado_backend.configure()

    config_file_list = [
        "Makefile",
        name + ".tcl",
        name + "_run.tcl",
        name + "_pgm.tcl",
    ]

    if synth_tool == "yosys":
        config_file_list.append("edalize_yosys_procs.tcl")
        config_file_list.append("edalize_yosys_template.tcl")
    else:
        config_file_list.append(name + "_synth.tcl")

    ref_dir = os.path.join(tests_dir, "test_" + tool, test_name)
    compare_files(ref_dir, work_root, config_file_list)

    build_file_list = ["vivado.cmd"]

    if synth_tool == "yosys":
        build_file_list.append("yosys.cmd")

    vivado_backend.build()
    compare_files(ref_dir, work_root, build_file_list)


def test_vivado_board_file(make_edalize_test):
    tf = make_edalize_test(
        "vivado",
        ref_dir="board_file",
        param_types=["generic", "vlogdefine", "vlogparam"],
        tool_options={
            "part": "xc7a35tcsg324-1",
            "board_part": "em.avnet.com:mini_itx_7z100:part0:1.0",
            "board_repo_paths": ["./board_repo"],
        },
    )
    tf.backend.configure()
    tf.compare_files(
        [
            "Makefile",
            tf.test_name + ".tcl",
            tf.test_name + "_synth.tcl",
            tf.test_name + "_run.tcl",
            tf.test_name + "_pgm.tcl",
        ]
    )

    tf.backend.build()
    tf.compare_files(["vivado.cmd"])
