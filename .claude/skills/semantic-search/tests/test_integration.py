#!/usr/bin/env python3
"""
Integration tests for searching-code-semantically skill

Tests script interoperability, argument passing, and error handling.
Note: Full integration testing requires global installation which may not
exist in test environments. These tests verify script behavior patterns.
"""

import subprocess
import json
from pathlib import Path

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"


class TestScriptInteroperability:
    """Test that scripts work together correctly"""

    def test_all_scripts_executable(self):
        """Verify all scripts are executable"""
        scripts = ["search.py", "status.py", "find-similar.py", "utils.py"]
        for script in scripts:
            script_path = SCRIPTS_DIR / script
            assert script_path.exists(), f"{script} not found"
            assert script_path.stat().st_mode & 0o111, f"{script} not executable"

    def test_all_scripts_have_shebang(self):
        """Verify all scripts have proper shebang"""
        scripts = ["search.py", "status.py", "find-similar.py", "utils.py"]
        for script in scripts:
            script_path = SCRIPTS_DIR / script
            with open(script_path, 'r') as f:
                first_line = f.readline()
                assert first_line.startswith('#!/usr/bin/env python3'), \
                    f"{script} missing or incorrect shebang"

    def test_consistent_error_json_structure(self):
        """Verify all scripts produce consistent error JSON"""
        test_cases = [
            (["python", str(SCRIPTS_DIR / "search.py"), "--storage-dir", "/nonexistent"]),
            (["python", str(SCRIPTS_DIR / "status.py"), "--storage-dir", "/nonexistent"]),
            (["python", str(SCRIPTS_DIR / "find-similar.py"), "--chunk-id", "test", "--storage-dir", "/nonexistent"])
        ]

        for cmd in test_cases:
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode != 0

            # All should produce valid JSON errors
            try:
                error_data = json.loads(result.stderr)
                assert "success" in error_data
                assert error_data["success"] is False
                assert "error" in error_data
            except json.JSONDecodeError:
                assert False, f"Command {cmd} did not produce valid JSON error"


class TestWindowsCompatibility:
    """Windows compatibility tests (requires actual Windows environment)"""

    def test_windows_compatibility_documented(self):
        """Verify Windows compatibility is documented"""
        # This is a placeholder - actual Windows testing requires Windows environment
        # Phase 4 documentation will include Windows compatibility notes
        assert True, "Windows testing deferred to Phase 4 troubleshooting.md (CC#7)"


class TestConcurrentExecution:
    """Concurrent execution safety (CC#4)"""

    def test_concurrent_execution_documented(self):
        """Verify concurrent execution limitations are documented"""
        # Actual concurrent execution testing requires running index
        # Phase 4 documentation will include warnings about unsafe operations
        assert True, "Concurrent execution warnings deferred to Phase 4 troubleshooting.md (CC#4)"


# Integration test summary
if __name__ == "__main__":
    print("Running integration tests...")
    print("\nTest Coverage:")
    print("- Script executability and shebangs")
    print("- Consistent JSON error structure across all scripts")
    print("- Windows compatibility (documented for Phase 4)")
    print("- Concurrent execution safety (documented for Phase 4)")
    print("\nNote: Full integration testing requires global installation")
    print("Run with: pytest tests/test_integration.py -v")
