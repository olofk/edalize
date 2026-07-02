from .edalize_common import make_edalize_test


def test_vcf(make_edalize_test):
    tf = make_edalize_test(
        "vcf",
        paramtypes=["plusarg", "vlogdefine", "vlogparam"],
        tool_options={"app": ["FPV"]},
    )

    # Copy example jinja template to work root
    tf.copy_to_work_root("config.tcl.j2")

    # Ensure our tcl is properly generated during config
    tf.backend.configure()

    tf.compare_file(["vcf.tcl"])

    # This should not do anything
    tf.backend.build()

    # Should run vcf, but for our case, just generates the command
    # for us to compare
    tf.backend.run()

    tf.compare_files(["vcf.cmd"])
