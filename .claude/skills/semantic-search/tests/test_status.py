#!/usr/bin/env python3
"""Unit tests for status.py"""

import json
import subprocess
import pytest
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
STATUS_PY = SCRIPTS_DIR / "status.py"

# Skip all tests if status.py doesn't exist (unimplemented feature)
pytestmark = pytest.mark.skipif(
    not STATUS_PY.exists(),
    reason="status.py not implemented"
)


class TestStatusArgumentParsing:
    """Test status.py argument parsing"""

    def test_status_accepts_no_args(self):
        """Test status.py runs with default arguments"""
        result = subprocess.run(
            ["python", str(STATUS_PY)],
            capture_output=True,
            text=True
        )
        # May fail due to missing installation, but args should parse
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()

    def test_status_accepts_custom_storage_dir(self):
        """Test status.py accepts --storage-dir parameter"""
        result = subprocess.run(
            ["python", str(STATUS_PY), "--storage-dir", "/tmp/test-index"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()


class TestStatusJSONOutput:
    """Test status.py JSON output structure"""

    def test_status_error_produces_json(self):
        """Test status.py produces valid JSON error output"""
        result = subprocess.run(
            ["python", str(STATUS_PY), "--storage-dir", "/nonexistent/path"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

        try:
            error_data = json.loads(result.stderr)
            assert "success" in error_data
            assert error_data["success"] is False
            assert "error" in error_data
        except json.JSONDecodeError:
            pytest.fail("stderr did not contain valid JSON")

    def test_status_missing_index_helpful_error(self):
        """Test status.py provides helpful error for missing index"""
        result = subprocess.run(
            ["python", str(STATUS_PY), "--storage-dir", "/nonexistent/index"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

        try:
            error_data = json.loads(result.stderr)
            assert error_data["success"] is False
            assert "suggestion" in error_data or "index" in str(error_data).lower()
        except json.JSONDecodeError:
            pytest.fail("Error output was not valid JSON")


if __name__ == "__main__":
    print("Running status.py unit tests...")
    print("Test Coverage: Argument parsing, JSON output, error handling")
    print("Run with: pytest tests/test_status.py -v")
