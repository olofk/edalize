from .edalize_tool_common import tool_fixture

# Run / run-options
def test_tool_vcs_2_stage(tool_fixture):

    tool_options = {
        "2_stage_flow": True,
        "analysis_options": ["several", "analysis", "options"],
        "vcs_options": ["some", "vcs", "options"],
        "run_options": ["and", "some", "run", "options"],
    }

    tf = tool_fixture("vcs", tool_options=tool_options, ref_subdir="2stage_basic")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "vcs.f",
            "parameters.txt",
        ]
    )


def test_tool_vcs_2_stage_minimal(tool_fixture):
    tool_options = {
        "2_stage_flow": True,
    }
    tf = tool_fixture(
        "vcs", tool_options=tool_options, paramtypes=[], ref_subdir="2stage_minimal"
    )

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "vcs.f",
            "parameters.txt",
        ]
    )


def test_tool_vcs_3_stage(tool_fixture):

    tool_options = {
        "2_stage_flow": False,
        "binary_name": "custom_binary_name",
        "analysis_options": ["several", "analysis", "options"],
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
            "libx.f",
            "vcs.f",
            "work.f",
            "work_1.f",
            "work_2.f",
            "work_3.f",
            "work_4.f",
            "work_5.f",
            "work_6.f",
            "parameters.txt",
        ]
    )


def test_tool_vcs_unr(tool_fixture):
    tool_options = {
        "vcs_unr_cfg_file": "my_unr_config.cfg",
    }
    tf = tool_fixture("vcs", tool_options=tool_options, paramtypes=[], ref_subdir="unr")

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "libx.f",
            "vcs.f",
            "work.f",
            "work_1.f",
            "work_2.f",
            "work_3.f",
            "work_4.f",
            "work_5.f",
            "work_6.f",
            "parameters.txt",
        ]
    )


def test_tool_vcs_synopsys_sim_setup(tool_fixture):
    files = [
        {"name": "sv_file.sv", "file_type": "systemVerilogSource"},
        {"name": "my_setup.setup", "file_type": "synopsys_sim_setup"},
        {"name": "extra_setup.setup", "file_type": "synopsys_sim_setup"},
        {"name": "vhdl_lfile", "file_type": "vhdlSource", "logical_name": "libx"},
    ]
    tf = tool_fixture(
        "vcs",
        files=files,
        paramtypes=[],
        ref_subdir="synopsys_sim_setup",
    )

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "libx.f",
            "vcs.f",
            "work.f",
            "parameters.txt",
        ]
    )


def test_tool_vcs_3_stage_minimal(tool_fixture):
    tf = tool_fixture("vcs", paramtypes=[], ref_subdir="minimal")

    name = "design"

    tf.tool.configure()
    tf.compare_config_files(
        [
            "synopsys_sim.setup",
            "libx.f",
            "vcs.f",
            "work.f",
            "work_1.f",
            "work_2.f",
            "work_3.f",
            "work_4.f",
            "work_5.f",
            "work_6.f",
            "parameters.txt",
        ]
    )
