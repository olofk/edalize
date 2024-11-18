from .edalize_tool_common import tool_fixture

# TODO: File-specific defines
# Run / run-options
def test_tool_vcs(tool_fixture):

    tool_options = {
        "vlogan_options": ["a", "few", "vlogan", "options"],
        "vhdlan_options": ["also", "vhdlan", "options"],
        "vcs_options": ["some", "vcs", "options"],
        "run_options": ["and", "some", "run", "options"],
    }

    tf = tool_fixture("vcs", tool_options=tool_options, ref_subdir="basic")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "libx.1.f",
            "vcs.f",
            "work.1.f",
            "work.2.f",
            "work.3.f",
            "parameters.txt",
        ]
    )


def test_tool_vcs_minimal(tool_fixture):
    tf = tool_fixture("vcs", ref_subdir="minimal")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "libx.1.f",
            "vcs.f",
            "work.1.f",
            "work.2.f",
            "work.3.f",
            "parameters.txt",
        ]
    )
