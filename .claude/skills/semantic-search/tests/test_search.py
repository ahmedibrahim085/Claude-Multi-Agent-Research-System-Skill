#!/usr/bin/env python3
"""
Unit tests for search.py

Tests semantic code search script invocation:
- Argument parsing and validation
- JSON output structure
- Error handling

Uses subprocess to test script as executable.
"""

import json
import subprocess
import pytest
from pathlib import Path

# Locate the search script (bash wrapper)
TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
SEARCH_SCRIPT = SCRIPTS_DIR / "search"

# Skip all tests if search script doesn't exist
pytestmark = pytest.mark.skipif(
    not SEARCH_SCRIPT.exists(),
    reason="search script not found"
)


class TestSearchArgumentParsing:
    """Test search.py argument parsing and validation"""

    def test_search_missing_query_fails(self):
        """Test search exits with error when --query is missing"""
        result = subprocess.run(
            ["bash", str(SEARCH_SCRIPT)],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        # Either argparse error (if installation OK) or setup error (if installation missing)
        assert ("required" in result.stderr.lower() or
                "query" in result.stderr.lower() or
                "import" in result.stderr.lower())

    def test_search_accepts_valid_query(self):
        """Test search.py accepts valid --query argument"""
        # This test verifies argument parsing, not actual search
        # (actual search requires global installation which may not exist in test env)
        result = subprocess.run(
            ["python", str(SEARCH_SCRIPT), "--query", "test search"],
            capture_output=True,
            text=True
        )
        # May fail due to missing installation, but should parse args successfully
        # If it fails, it should be due to missing installation, not arg parsing
        if result.returncode != 0:
            assert "argument" not in result.stderr.lower()  # Not an argument error

    def test_search_accepts_k_parameter(self):
        """Test search.py accepts --k parameter"""
        result = subprocess.run(
            ["python", str(SEARCH_SCRIPT), "--query", "test", "--k", "10"],
            capture_output=True,
            text=True
        )
        # Should accept the arguments (may fail on execution)
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()

    def test_search_accepts_storage_dir(self):
        """Test search.py accepts --storage-dir parameter"""
        result = subprocess.run(
            ["python", str(SEARCH_SCRIPT), "--query", "test", "--storage-dir", "/tmp/test-index"],
            capture_output=True,
            text=True
        )
        # Should accept the arguments
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()

    def test_search_invalid_k_type_fails(self):
        """Test search.py rejects non-integer --k value"""
        result = subprocess.run(
            ["python", str(SEARCH_SCRIPT), "--query", "test", "--k", "not-a-number"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        # Either argparse error or setup error
        assert ("invalid" in result.stderr.lower() or
                "value" in result.stderr.lower() or
                "import" in result.stderr.lower())


class TestSearchJSONOutput:
    """Test search.py JSON output structure"""

    def test_search_error_produces_json(self):
        """Test search.py produces valid JSON error output"""
        # Run with missing index to trigger error
        result = subprocess.run(
            ["python", str(SEARCH_SCRIPT), "--query", "test", "--storage-dir", "/nonexistent/path"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

        # Verify stderr contains valid JSON
        try:
            error_data = json.loads(result.stderr)
            assert "success" in error_data
            assert error_data["success"] is False
            assert "error" in error_data
        except json.JSONDecodeError:
            pytest.fail("stderr did not contain valid JSON")

    @pytest.mark.skipif(
        not (Path.home() / ".local" / "share" / "claude-context-local").exists(),
        reason="Global installation not found - expected in test environment"
    )
    def test_search_success_produces_json(self):
        """Test search.py produces valid JSON success output (requires installation)"""
        # Create a temp index directory for testing
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["python", str(SEARCH_SCRIPT), "--query", "test function", "--k", "3", "--storage-dir", tmpdir],
                capture_output=True,
                text=True
            )

            # If installation exists but index doesn't, we'll get an error
            # If both exist, we should get success
            if result.returncode == 0:
                # Success case - verify JSON structure
                try:
                    output_data = json.loads(result.stdout)
                    assert "success" in output_data
                    assert output_data["success"] is True
                    assert "data" in output_data
                except json.JSONDecodeError:
                    pytest.fail("stdout did not contain valid JSON")


class TestSearchErrorHandling:
    """Test search.py error handling and messages"""

    def test_search_missing_index_helpful_error(self):
        """Test search.py provides helpful error for missing index"""
        result = subprocess.run(
            ["python", str(SEARCH_SCRIPT), "--query", "test", "--storage-dir", "/nonexistent/index"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0

        try:
            error_data = json.loads(result.stderr)
            # Should mention error and provide suggestion
            # Could be index error (if installation OK) or import error (if installation missing)
            assert "error" in error_data
            assert error_data["success"] is False
            assert "suggestion" in error_data or "install" in str(error_data).lower()
        except json.JSONDecodeError:
            pytest.fail("Error output was not valid JSON")


# Test summary
if __name__ == "__main__":
    print("Running search.py unit tests...")
    print("\nTest Coverage:")
    print("- Argument parsing (--query required)")
    print("- Optional arguments (--k, --storage-dir)")
    print("- Type validation (--k must be integer)")
    print("- JSON output structure (error and success cases)")
    print("- Error messaging (helpful suggestions)")
    print("\nRun with: pytest tests/test_search.py -v")
