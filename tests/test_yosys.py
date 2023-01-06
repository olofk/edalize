from .edalize_common import make_edalize_test


def test_symbiyosys(make_edalize_test):
    output_names = {
        "default_output_name": {
            "arch": "ice40",
        },
        "custom_output_name": {"arch": "ice40", "output_name": "test.json"},
    }

    for test_name, tool_options in output_names.items():
        tf = make_edalize_test(
            "yosys",
            param_types=["vlogdefine", "vlogparam"],
            tool_options=tool_options,
            ref_dir=test_name,
        )

        tf.backend.configure()
        tf.compare_files(["Makefile"])
