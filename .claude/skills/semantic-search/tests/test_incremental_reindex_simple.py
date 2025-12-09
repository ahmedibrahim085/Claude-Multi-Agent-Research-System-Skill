#!/usr/bin/env python3
"""
Lightweight tests for incremental_reindex.py

Tests Option A.25 implementation WITHOUT importing the module
(avoids dependency issues while still verifying critical changes)

Tests:
- max_age parameter default value (360 minutes)
- argparse default value (360 minutes)
- Function signature verification

Run with: pytest .claude/skills/semantic-search/tests/test_incremental_reindex_simple.py -v
"""

import pytest
import re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════════

TESTS_DIR = Path(__file__).parent
SCRIPT_PATH = TESTS_DIR.parent / "scripts" / "incremental_reindex.py"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: needs_reindex() DEFAULT PARAMETER
# ═══════════════════════════════════════════════════════════════════════════

def test_needs_reindex_default_is_360():
    """Test that needs_reindex() has default max_age_minutes=360"""
    # Read the source file
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find the function definition
    pattern = r'def needs_reindex\(self,\s*max_age_minutes:\s*float\s*=\s*(\d+)\)'
    match = re.search(pattern, content)

    assert match is not None, "Could not find needs_reindex function definition"

    default_value = int(match.group(1))
    assert default_value == 360, \
        f"needs_reindex default should be 360, got {default_value}"


def test_needs_reindex_not_old_value_60():
    """Test that needs_reindex does NOT have old default of 60"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Check it's not using old value
    pattern = r'def needs_reindex\(self,\s*max_age_minutes:\s*float\s*=\s*60\)'
    match = re.search(pattern, content)

    assert match is None, \
        "needs_reindex should NOT have default=60 (old value)"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: ARGPARSE DEFAULT
# ═══════════════════════════════════════════════════════════════════════════

def test_argparse_default_is_360():
    """Test that argparse --max-age default is 360"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find the argparse add_argument line
    pattern = r"add_argument\s*\(\s*'--max-age'[^)]*default\s*=\s*(\d+)"
    match = re.search(pattern, content)

    assert match is not None, "Could not find --max-age argument definition"

    default_value = int(match.group(1))
    assert default_value == 360, \
        f"argparse --max-age default should be 360, got {default_value}"


def test_argparse_help_text_mentions_360():
    """Test that argparse help text mentions default: 360"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find the help text for --max-age
    pattern = r"add_argument\s*\(\s*'--max-age'[^)]*help\s*=\s*['\"]([^'\"]*)['\"]"
    match = re.search(pattern, content)

    assert match is not None, "Could not find --max-age help text"

    help_text = match.group(1)
    assert "360" in help_text, \
        f"Help text should mention 360, got: {help_text}"


def test_argparse_not_old_value_60():
    """Test that argparse does NOT use old default of 60"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Check it's not using old value
    pattern = r"add_argument\s*\(\s*'--max-age'[^)]*default\s*=\s*60\b"
    match = re.search(pattern, content)

    assert match is None, \
        "argparse --max-age should NOT have default=60 (old value)"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: AGE CONVERSION MATH
# ═══════════════════════════════════════════════════════════════════════════

def test_age_check_uses_multiplication_by_60():
    """Test that age check correctly multiplies minutes by 60 for seconds"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find the age comparison logic
    pattern = r'age\s*>\s*max_age_minutes\s*\*\s*60'
    match = re.search(pattern, content)

    assert match is not None, \
        "Age check should use 'age > max_age_minutes * 60' conversion"


def test_age_check_not_hardcoded():
    """Test that age check is NOT hardcoded to 60 or 360 minutes"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the needs_reindex function
    func_start = content.find('def needs_reindex')
    func_end = content.find('\n    def ', func_start + 1)
    if func_end == -1:
        func_end = len(content)
    function_body = content[func_start:func_end]

    # Check it doesn't hardcode the threshold in minutes
    bad_patterns = [
        r'age\s*>\s*21600',  # 360 * 60 hardcoded
        r'age\s*>\s*3600',   # 60 * 60 hardcoded
    ]

    for pattern in bad_patterns:
        match = re.search(pattern, function_body)
        assert match is None, \
            f"Age check should not hardcode seconds value, found: {pattern}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: FILE STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

def test_script_file_exists():
    """Test that incremental_reindex.py exists"""
    assert SCRIPT_PATH.exists(), \
        f"Script not found at {SCRIPT_PATH}"


def test_script_is_executable():
    """Test that script has execute permissions"""
    assert SCRIPT_PATH.stat().st_mode & 0o111, \
        "Script should be executable"


def test_script_has_shebang():
    """Test that script has correct shebang"""
    with open(SCRIPT_PATH, 'r') as f:
        first_line = f.readline()

    assert first_line.startswith('#!/usr/bin/env python3'), \
        f"Script should have python3 shebang, got: {first_line}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST: DOCUMENTATION COMMENTS
# ═══════════════════════════════════════════════════════════════════════════

def test_docstring_documents_behavior():
    """Test that needs_reindex docstring exists and documents age check"""
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find needs_reindex function
    func_start = content.find('def needs_reindex')
    assert func_start != -1, "needs_reindex function not found"

    # Check for docstring
    docstring_start = content.find('"""', func_start)
    docstring_end = content.find('"""', docstring_start + 3)

    assert docstring_start != -1 and docstring_end != -1, \
        "needs_reindex should have a docstring"


# ═══════════════════════════════════════════════════════════════════════════
# TEST SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Lightweight tests for incremental_reindex.py")
    print("\nTest Coverage (without importing module):")
    print("- needs_reindex() default parameter (360 minutes)")
    print("- argparse --max-age default (360 minutes)")
    print("- Age conversion math (* 60 for seconds)")
    print("- No hardcoded values")
    print("- File structure and permissions")
    print("\nRun with: pytest test_incremental_reindex_simple.py -v")
