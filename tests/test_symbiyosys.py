from edalize_common import make_edalize_test


def test_symbiyosys(make_edalize_test):
    tf = make_edalize_test('symbiyosys',
                           param_types=['vlogdefine', 'vlogparam'],
                           tool_options={
                               'tasknames': ['task0', 'task1'],
                           })

    # Copy our example configuration file to the work root. The name matches an
    # entry in edalize_common's FILES list. Note that we chose a name that
    # doesn't collide with test.sby (the file that the tool generates, in the
    # same directory).
    tf.copy_to_work_root('config.sby.j2')

    tf.backend.configure()

    # The configure step is supposed to interpolate the .sby file and dump
    # lists of RTL files and include directories. (These are needed if you want
    # to use sv2v as a fusesoc pre_build hook).
    tf.compare_files(['test.sby', 'files.txt', 'incdirs.txt'])

    # The 'build' step doesn't actually do anything, but we should run it to
    # check that nothing explodes.
    tf.backend.build()

    # The 'run' step runs sby. Our mock version dumps its command line
    # arguments to "sby.cmd".
    tf.backend.run()

    tf.compare_files(['sby.cmd'])
