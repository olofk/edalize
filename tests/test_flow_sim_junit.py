import pytest

from edalize.flows.sim import Sim

TESTSUITES_ROOT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="all">
    <testcase name="test_pass"/>
    <testcase name="test_fail"><failure message="boom"/></testcase>
  </testsuite>
</testsuites>
"""

TESTSUITE_ROOT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="all">
  <testcase name="test_pass"/>
  <testcase name="test_fail"><failure message="boom"/></testcase>
</testsuite>
"""

NESTED_TESTSUITES = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="outer">
    <testsuite name="inner">
      <testcase name="test_pass"/>
      <testcase name="test_fail"><error message="boom"/></testcase>
    </testsuite>
  </testsuite>
</testsuites>
"""

ALL_PASSING = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="all">
  <testcase name="test_pass"/>
</testsuite>
"""


def check(tmp_path, xml):
    results = tmp_path / "results.xml"
    results.write_text(xml)
    # The check only looks at the file, so it does not need a configured flow
    Sim._check_junit_xml(None, results)


@pytest.mark.parametrize(
    "xml",
    [TESTSUITES_ROOT, TESTSUITE_ROOT, NESTED_TESTSUITES],
    ids=["testsuites_root", "testsuite_root", "nested_testsuites"],
)
def test_failures_are_detected(tmp_path, xml):
    """A failure must be reported whatever the suites look like."""
    with pytest.raises(RuntimeError) as e:
        check(tmp_path, xml)

    assert "Failed 1 of 2 tests" in str(e.value)


def test_passing_results_do_not_raise(tmp_path):
    check(tmp_path, ALL_PASSING)
