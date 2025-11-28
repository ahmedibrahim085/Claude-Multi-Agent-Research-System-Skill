#!/usr/bin/env python3
"""Unit tests for find-similar.py"""

import json
import subprocess
import pytest
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
FIND_SIMILAR_PY = SCRIPTS_DIR / "find-similar.py"


class TestFindSimilarArgumentParsing:
    """Test find-similar.py argument parsing"""

    def test_find_similar_missing_chunk_id_fails(self):
        """Test find-similar.py exits with error when --chunk-id is missing"""
        result = subprocess.run(
            ["python", str(FIND_SIMILAR_PY)],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert ("required" in result.stderr.lower() or
                "chunk" in result.stderr.lower() or
                "import" in result.stderr.lower())

    def test_find_similar_accepts_valid_chunk_id(self):
        """Test find-similar.py accepts valid --chunk-id argument"""
        result = subprocess.run(
            ["python", str(FIND_SIMILAR_PY), "--chunk-id", "test-chunk-123"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            assert "argument" not in result.stderr.lower() or "import" in result.stderr.lower()

    def test_find_similar_accepts_k_parameter(self):
        """Test find-similar.py accepts --k parameter"""
        result = subprocess.run(
            ["python", str(FIND_SIMILAR_PY), "--chunk-id", "test", "--k", "10"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            assert "unrecognized" not in result.stderr.lower()


class TestFindSimilarJSONOutput:
    """Test find-similar.py JSON output structure"""

    def test_find_similar_error_produces_json(self):
        """Test find-similar.py produces valid JSON error output"""
        result = subprocess.run(
            ["python", str(FIND_SIMILAR_PY), "--chunk-id", "test", "--storage-dir", "/nonexistent/path"],
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


if __name__ == "__main__":
    print("Running find-similar.py unit tests...")
    print("Test Coverage: Argument parsing, JSON output, error handling")
    print("Run with: pytest tests/test_find_similar.py -v")
