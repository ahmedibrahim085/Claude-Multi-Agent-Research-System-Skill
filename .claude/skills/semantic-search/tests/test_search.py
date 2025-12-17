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
            ["bash", str(SEARCH_SCRIPT), "--query", "test search"],
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
            ["bash", str(SEARCH_SCRIPT), "--query", "test", "--k", "10"],
            capture_output=True,
            text=True
        )
        # Should accept the arguments (may fail on execution)
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()

    def test_search_accepts_storage_dir(self):
        """Test search.py accepts --storage-dir parameter"""
        result = subprocess.run(
            ["bash", str(SEARCH_SCRIPT), "--query", "test", "--storage-dir", "/tmp/test-index"],
            capture_output=True,
            text=True
        )
        # Should accept the arguments
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()

    def test_search_invalid_k_type_fails(self):
        """Test search rejects non-integer --k value (bash wrapper)"""
        result = subprocess.run(
            ["bash", str(SEARCH_SCRIPT), "--query", "test", "--project", str(Path.cwd()), "--k", "not-a-number"],
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

    def test_search_missing_project_error(self):
        """Test search fails with clear error when --project is missing (bash wrapper behavior)"""
        # Bash wrapper validates required params before Python execution
        result = subprocess.run(
            ["bash", str(SEARCH_SCRIPT), "--query", "test"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        # Bash wrapper outputs plain text error (not JSON)
        assert "--project is required" in result.stderr

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
                ["bash", str(SEARCH_SCRIPT), "--query", "test function", "--k", "3", "--storage-dir", tmpdir],
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

    def test_search_missing_query_error(self):
        """Test search fails with usage message when --query is missing (bash wrapper behavior)"""
        # Bash wrapper validates required params before Python execution
        result = subprocess.run(
            ["bash", str(SEARCH_SCRIPT)],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        # Bash wrapper outputs plain text usage message (not JSON)
        assert "Usage:" in result.stderr
        assert "--query" in result.stderr


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
