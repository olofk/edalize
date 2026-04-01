import os
from unittest.mock import patch, MagicMock
import subprocess

import pytest


# ── Legacy API ──────────────────────────────────────────────────────────


def _make_legacy_tool(work_root):
    """Create a minimal legacy Edatool instance with enough state to call _run_tool."""
    from edalize.edatool import Edatool

    obj = object.__new__(Edatool)
    obj.work_root = str(work_root)
    obj.verbose = False
    obj.stdout = None
    obj.stderr = None
    return obj


@patch("edalize.edatool.run")
def test_legacy_run_tool_prints_dir_notifications(mock_run, tmp_path, capsys):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["true"], returncode=0, stdout=None, stderr=None
    )

    tool = _make_legacy_tool(tmp_path)
    tool._run_tool("true")

    captured = capsys.readouterr().out
    abs_path = str(os.path.abspath(tmp_path))
    assert f"Entering directory '{abs_path}'" in captured
    assert f"Leaving directory '{abs_path}'" in captured


@patch("edalize.edatool.run")
def test_legacy_run_tool_no_leaving_on_error(mock_run, tmp_path, capsys):
    mock_run.side_effect = FileNotFoundError("not found")

    tool = _make_legacy_tool(tmp_path)
    with pytest.raises(RuntimeError):
        tool._run_tool("nonexistent_cmd")

    captured = capsys.readouterr().out
    abs_path = str(os.path.abspath(tmp_path))
    assert f"Entering directory '{abs_path}'" in captured
    assert "Leaving directory" not in captured


# ── Flow API ────────────────────────────────────────────────────────────


def _make_flow_tool():
    """Create a minimal Edaflow-like object to test _run_tool."""
    from edalize.flows.edaflow import Edaflow

    obj = object.__new__(Edaflow)
    obj.verbose = False
    obj.stdout = None
    obj.stderr = None
    return obj


@patch("edalize.flows.edaflow.run")
def test_flow_run_tool_prints_dir_notifications(mock_run, tmp_path, capsys):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["true"], returncode=0, stdout=None, stderr=None
    )

    flow = _make_flow_tool()
    flow._run_tool("true", cwd=str(tmp_path))

    captured = capsys.readouterr().out
    abs_path = str(os.path.abspath(tmp_path))
    assert f"Entering directory '{abs_path}'" in captured
    assert f"Leaving directory '{abs_path}'" in captured


@patch("edalize.flows.edaflow.run")
def test_flow_run_tool_no_leaving_on_error(mock_run, tmp_path, capsys):
    mock_run.side_effect = FileNotFoundError("not found")

    flow = _make_flow_tool()
    with pytest.raises(RuntimeError):
        flow._run_tool("nonexistent_cmd", cwd=str(tmp_path))

    captured = capsys.readouterr().out
    abs_path = str(os.path.abspath(tmp_path))
    assert f"Entering directory '{abs_path}'" in captured
    assert "Leaving directory" not in captured


@patch("edalize.flows.edaflow.run")
def test_flow_run_tool_no_cwd_skips_notifications(mock_run, capsys):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["true"], returncode=0, stdout=None, stderr=None
    )

    flow = _make_flow_tool()
    flow._run_tool("true")

    captured = capsys.readouterr().out
    assert "Entering directory" not in captured
    assert "Leaving directory" not in captured
