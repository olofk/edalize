import pytest
import sys

from edalize_common import make_edalize_test


def test_vtr(make_edalize_test):
    tf = make_edalize_test('vtr')

    tf.backend.configure()
    tf.compare_files(['Makefile'])

    tf.backend.build()
    tf.compare_files(['run_vtr_flow.py.cmd'])
