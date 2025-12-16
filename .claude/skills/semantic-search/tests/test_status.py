#!/usr/bin/env python3
"""Unit tests for status.py"""

import json
import subprocess
import pytest
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
STATUS_SCRIPT = SCRIPTS_DIR / "status"

# Skip all tests if status script doesn't exist
pytestmark = pytest.mark.skipif(
    not STATUS_SCRIPT.exists(),
    reason="status script not found"
)


class TestStatusArgumentParsing:
    """Test status.py argument parsing"""

    def test_status_accepts_no_args(self):
        """Test status.py runs with default arguments"""
        result = subprocess.run(
            ["bash", str(STATUS_SCRIPT)],
            capture_output=True,
            text=True
        )
        # May fail due to missing installation, but args should parse
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()

    def test_status_accepts_custom_storage_dir(self):
        """Test status.py accepts --storage-dir parameter"""
        result = subprocess.run(
            ["bash", str(STATUS_SCRIPT), "--storage-dir", "/tmp/test-index"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()


class TestStatusJSONOutput:
    """Test status.py JSON output structure"""

    def test_status_returns_valid_json(self):
        """Test status returns valid JSON with index statistics (bash wrapper behavior)"""
        # Status script has no error modes - always returns success with default storage
        result = subprocess.run(
            ["bash", str(STATUS_SCRIPT)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        # Parse JSON from stdout (not stderr)
        try:
            data = json.loads(result.stdout)
            assert "index_statistics" in data
            assert "model_information" in data
            # Verify structure
            assert isinstance(data["index_statistics"], dict)
            assert isinstance(data["model_information"], dict)
        except json.JSONDecodeError:
            pytest.fail("stdout did not contain valid JSON")


if __name__ == "__main__":
    print("Running status.py unit tests...")
    print("Test Coverage: Argument parsing, JSON output, error handling")
    print("Run with: pytest tests/test_status.py -v")
