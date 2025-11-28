#!/usr/bin/env python3
"""
Unit tests for utils.py

Tests all 3 utility functions:
- setup(): Import validation and global installation detection
- error_exit(): JSON error output formatting
- success(): JSON success output formatting

Addresses CC#9 (utils.py as single point of failure)
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add scripts directory to path for imports
TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from utils import setup, error_exit, success


class TestSetup:
    """Test setup() function for global installation validation"""

    def test_setup_with_valid_install(self):
        """Test setup succeeds when global installation exists with valid modules"""
        # This test requires actual global installation
        # If not installed, test will verify error handling instead
        try:
            IntelligentSearcher, CodeIndexManager = setup()
            # If we get here, installation exists
            assert IntelligentSearcher is not None
            assert CodeIndexManager is not None
        except SystemExit:
            # Installation doesn't exist - this is expected in test environments
            pytest.skip("Global installation not found - expected in test environment")

    def test_setup_without_install_exits(self):
        """Test setup exits gracefully when installation missing"""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                # Capture stderr to prevent test output pollution
                with patch('sys.stderr', new_callable=StringIO):
                    setup()
            assert exc_info.value.code == 1

    def test_setup_without_install_outputs_json(self):
        """Test setup outputs valid JSON error when installation missing"""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit):
                    setup()

                error_output = mock_stderr.getvalue()
                error_data = json.loads(error_output)

                assert error_data["success"] is False
                assert "error" in error_data
                assert "Global installation not found" in error_data["error"]
                assert "install_path" in error_data
                assert "install_cmd" in error_data


class TestErrorExit:
    """Test error_exit() function for structured error output"""

    def test_error_exit_exits_with_code_1(self):
        """Test error_exit() terminates with exit code 1"""
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.stderr', new_callable=StringIO):
                error_exit("Test error")
        assert exc_info.value.code == 1

    def test_error_exit_output_structure(self):
        """Test error_exit() produces valid JSON with correct structure"""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit):
                error_exit("Test error message")

            error_output = mock_stderr.getvalue()
            error_data = json.loads(error_output)

            assert error_data["success"] is False
            assert error_data["error"] == "Test error message"

    def test_error_exit_with_kwargs(self):
        """Test error_exit() includes additional kwargs in output"""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit):
                error_exit(
                    "Test error",
                    suggestion="Try this fix",
                    code=404
                )

            error_output = mock_stderr.getvalue()
            error_data = json.loads(error_output)

            assert error_data["success"] is False
            assert error_data["error"] == "Test error"
            assert error_data["suggestion"] == "Try this fix"
            assert error_data["code"] == 404

    def test_error_exit_writes_to_stderr(self):
        """Test error_exit() writes to stderr (not stdout)"""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    error_exit("Error message")

                assert len(mock_stderr.getvalue()) > 0
                assert len(mock_stdout.getvalue()) == 0


class TestSuccess:
    """Test success() function for structured success output"""

    def test_success_output_structure(self):
        """Test success() produces valid JSON with correct structure"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            success({"result": "data"})

            output = mock_stdout.getvalue()
            data = json.loads(output)

            assert data["success"] is True
            assert "data" in data
            assert data["data"] == {"result": "data"}

    def test_success_with_dict_data(self):
        """Test success() handles dictionary data correctly"""
        test_data = {
            "files": ["file1.py", "file2.py"],
            "count": 2
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            success(test_data)

            output = mock_stdout.getvalue()
            data = json.loads(output)

            assert data["success"] is True
            assert data["data"] == test_data

    def test_success_with_list_data(self):
        """Test success() handles list data correctly"""
        test_data = [1, 2, 3, 4, 5]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            success(test_data)

            output = mock_stdout.getvalue()
            data = json.loads(output)

            assert data["success"] is True
            assert data["data"] == test_data

    def test_success_writes_to_stdout(self):
        """Test success() writes to stdout (not stderr)"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                success({"test": "data"})

                assert len(mock_stdout.getvalue()) > 0
                assert len(mock_stderr.getvalue()) == 0


class TestCrossplatformBehavior:
    """Test cross-platform path handling (CC#7)"""

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows path test requires Windows platform")
    def test_windows_path_detection(self):
        """Test setup() uses correct Windows path when os.name is 'nt'"""
        # This test requires actual Windows platform to avoid Path instantiation issues
        with patch('pathlib.Path.exists', return_value=False):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit):
                    setup()

                error_output = mock_stderr.getvalue()
                error_data = json.loads(error_output)

                # Verify Windows path in error message
                assert "AppData" in error_data["install_path"]
                assert "Local" in error_data["install_path"]

    def test_unix_path_detection(self):
        """Test setup() uses correct Unix path when os.name is 'posix'"""
        with patch('os.name', 'posix'):
            with patch('pathlib.Path.exists', return_value=False):
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    with pytest.raises(SystemExit):
                        setup()

                    error_output = mock_stderr.getvalue()
                    error_data = json.loads(error_output)

                    # Verify Unix path in error message
                    assert ".local" in error_data["install_path"]
                    assert "share" in error_data["install_path"]


# Test summary for validation
if __name__ == "__main__":
    print("Running utils.py unit tests...")
    print("\nTest Coverage:")
    print("- setup() with valid installation")
    print("- setup() without installation (error handling)")
    print("- setup() JSON error output")
    print("- error_exit() exit code")
    print("- error_exit() JSON structure")
    print("- error_exit() kwargs handling")
    print("- error_exit() stderr output")
    print("- success() JSON structure")
    print("- success() dict data handling")
    print("- success() list data handling")
    print("- success() stdout output")
    print("- Cross-platform: Windows path detection (CC#7)")
    print("- Cross-platform: Unix path detection (CC#7)")
    print("\nAddresses CC#9: utils.py as single point of failure")
    print("\nRun with: pytest tests/test_utils.py -v")
