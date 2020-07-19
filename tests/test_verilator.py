from edalize_common import make_edalize_test


def test_verilator_cc(make_edalize_test):
    mode = 'cc'
    tool_options = {
        'libs' : ['-lelf'],
        'mode' : mode,
        'verilator_options' : ['-Wno-fatal', '--trace'],
        'make_options' : ['OPT_FAST=-O2'],
    }
    tf = make_edalize_test('verilator',
                           param_types=['cmdlinearg', 'plusarg',
                                        'vlogdefine', 'vlogparam'],
                           tool_options=tool_options)

    tf.backend.configure()

    tf.compare_files(['Makefile'])
    tf.compare_files(['config.mk', tf.test_name + '.vc'], ref_subdir=mode)

    tf.copy_to_work_root('Vtop_module')
    tf.backend.run()

    tf.compare_files(['run.cmd'])


def test_verilator_sc(make_edalize_test):
    mode = 'sc'
    tf = make_edalize_test('verilator',
                           param_types=[],
                           tool_options={'mode': mode})

    tf.backend.configure()

    tf.compare_files(['Makefile'])
    tf.compare_files(['config.mk', tf.test_name + '.vc'], ref_subdir=mode)


def test_verilator_lint_only(make_edalize_test):
    mode = 'lint-only'
    tf = make_edalize_test('verilator',
                           param_types=[],
                           tool_options={'mode': mode})

    tf.backend.configure()

    tf.compare_files(['Makefile'])
    tf.compare_files(['config.mk', tf.test_name + '.vc'], ref_subdir=mode)
