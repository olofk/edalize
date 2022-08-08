import os
from .edalize_common import make_edalize_test, tests_dir


def test_openfpga(make_edalize_test):
    # Standard tool options
    tool_options = {
        "arch": "sofa-qlhd",
        "task_options": ["--debug"],
    }
    # Fake environment variables
    os.environ["OPENFPGA_PATH"] = "${{OPENFPGA_PATH}}"
    os.environ["SOFA_PATH"] = "${{SOFA_PATH}}"

    tf = make_edalize_test(
        tool_name="openfpga",
        test_name="test_openfpga_0",
        tool_options=tool_options,
    )

    tf.backend.configure()

    tf.compare_files(["config/task.conf"])
