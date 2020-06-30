from edalize_common import make_edalize_test
import os


def test_xsim(make_edalize_test):
    tool_options = {'xelab_options' : ['some', 'xelab_options'],
                    'xsim_options'  : ['a', 'few', 'xsim_options']}
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam', 'generic']

    tf = make_edalize_test('xsim',
                           tool_options=tool_options,
                           param_types=paramtypes)

    tf.backend.configure()
    tf.compare_files(['config.mk', 'Makefile', tf.test_name + '.prj'])

    tf.backend.build()
    tf.compare_files(['xelab.cmd'])

    xsimkdir = os.path.join(tf.work_root, 'xsim.dir', tf.test_name)
    os.makedirs(xsimkdir)
    with open(os.path.join(xsimkdir, 'xsimk'), 'w') as f:
        f.write("I am a compiled simulation kernel\n")
    tf.backend.run()

    tf.compare_files(['xsim.cmd'])
