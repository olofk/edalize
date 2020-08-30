from edalize_common import make_edalize_test
import os


def test_morty(make_edalize_test):
    tool_options = {'morty_options' : ['--prefix', 'blub']}
    paramtypes   = ['vlogdefine']

    tf = make_edalize_test('morty',
                           tool_options=tool_options,
                           param_types=paramtypes)

    tf.backend.build()
    tf.compare_files(['morty.cmd'])
