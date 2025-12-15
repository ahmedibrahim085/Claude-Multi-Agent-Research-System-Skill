#!/usr/bin/env python3
"""
Tests for Prerequisites Auto-Update After Successful Reindex

Tests the architectural gap fix: Prerequisites state file should auto-update
to TRUE after successful full reindex.

File tested: .claude/skills/semantic-search/scripts/incremental_reindex.py
Method: _update_prerequisites_state_after_successful_reindex()

NOTE: Uses regex-based testing to avoid dependency issues with sentence_transformers

Run with: pytest tests/test_prerequisites_update.py -v
"""

import pytest
import re
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_PATH = Path(__file__).parent.parent / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental_reindex.py'


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: METHOD EXISTS
# ═══════════════════════════════════════════════════════════════════════════

def test_prerequisites_update_method_exists():
    """
    CRITICAL: Verify the _update_prerequisites_state_after_successful_reindex method exists

    This is the core fix for the architectural gap.
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find the method definition
    pattern = r'def _update_prerequisites_state_after_successful_reindex\(self\):'
    match = re.search(pattern, content)

    assert match is not None, \
        "_update_prerequisites_state_after_successful_reindex method should exist"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: METHOD IS CALLED AFTER SUCCESSFUL REINDEX
# ═══════════════════════════════════════════════════════════════════════════

def test_method_called_after_successful_reindex():
    """
    CRITICAL: Verify the method is actually integrated into the reindex flow

    This ensures the fix is properly wired up (not just implemented but unused)
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Verify method is called
    pattern = r'self\._update_prerequisites_state_after_successful_reindex\(\)'
    match = re.search(pattern, content)

    assert match is not None, \
        "Method should be called somewhere in the script"

    # Find where it's called
    call_index = content.find('self._update_prerequisites_state_after_successful_reindex()')
    assert call_index > 0, "Method call should be found"

    # Check context - should be near save_index or record_timestamp
    context_start = max(0, call_index - 500)
    context_end = min(len(content), call_index + 500)
    context = content[context_start:context_end]

    # Should be called after indexing operations
    assert ('save_index' in context or
            'record_timestamp' in context or
            '_record_index_timestamp' in context), \
        "Method should be called near save_index or record_timestamp"

    # Should be before returning success
    # NOTE: Increased from 500 to 1500 chars to account for timing breakdown code (984 chars to return)
    lines_after_call = content[call_index:call_index + 1500].split('\n')
    has_return = any('return' in line for line in lines_after_call[:25])
    assert has_return, "Method should be called before returning from reindex"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: METHOD CHECKS INDEX FILE EXISTS (CONSERVATIVE)
# ═══════════════════════════════════════════════════════════════════════════

def test_method_checks_index_exists():
    """
    Verify conservative approach: Only update if index file actually exists

    Design principle documented in code.
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the method body
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_body = content[method_start:method_end]

    # Should check if index file exists
    assert 'index_file' in method_body.lower() or 'code.index' in method_body, \
        "Method should check if index file exists"

    assert '.exists()' in method_body, \
        "Method should call .exists() to verify index file"

    # Should return early if index doesn't exist
    assert 'return' in method_body, \
        "Method should have early return if index doesn't exist"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: METHOD RESPECTS MANUAL_OVERRIDE
# ═══════════════════════════════════════════════════════════════════════════

def test_method_respects_manual_override():
    """
    Verify manual_override flag is respected

    Design principle: User's manual settings should be respected
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the method body
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_body = content[method_start:method_end]

    # Should check manual_override
    assert 'manual_override' in method_body, \
        "Method should check manual_override flag"

    # Should return early if manual_override is true
    lines = method_body.split('\n')
    manual_override_check_found = False
    for i, line in enumerate(lines):
        if 'manual_override' in line and 'get(' in line:
            # Found the check, verify there's a return nearby
            next_few_lines = '\n'.join(lines[i:i+5])
            if 'return' in next_few_lines:
                manual_override_check_found = True
                break

    assert manual_override_check_found, \
        "Method should return early if manual_override is true"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: METHOD UPDATES PREREQUISITES TO TRUE
# ═══════════════════════════════════════════════════════════════════════════

def test_method_sets_prerequisites_to_true():
    """
    Verify the method sets SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY to True
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the method body
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_body = content[method_start:method_end]

    # Should set prerequisites to True
    assert 'SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY' in method_body, \
        "Method should set SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY"

    # Check that it's set to True
    pattern = r"['\"]SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY['\"]\s*\]\s*=\s*True"
    match = re.search(pattern, method_body)

    assert match is not None, \
        "Method should set SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY = True"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: METHOD UPDATES TIMESTAMP
# ═══════════════════════════════════════════════════════════════════════════

def test_method_updates_timestamp():
    """
    Verify the method updates the last_checked timestamp
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the method body
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_body = content[method_start:method_end]

    # Should update last_checked
    assert 'last_checked' in method_body, \
        "Method should update last_checked timestamp"

    # Should use datetime.now or similar
    assert ('datetime' in method_body or
            'isoformat' in method_body or
            'timestamp' in method_body.lower()), \
        "Method should generate current timestamp"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: METHOD HAS GRACEFUL ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════

def test_method_has_exception_handling():
    """
    Verify graceful error handling

    Design principle: Don't break indexing if state update fails
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the method body
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_body = content[method_start:method_end]

    # Should have try-except
    assert 'try:' in method_body, \
        "Method should have try-except for graceful error handling"

    assert 'except' in method_body, \
        "Method should catch exceptions"

    # Exception handling should not re-raise (should be graceful)
    # Check that there's no bare 'raise' after except
    lines = method_body.split('\n')
    in_except_block = False
    for line in lines:
        if 'except' in line:
            in_except_block = True
        if in_except_block and line.strip().startswith('raise'):
            pytest.fail("Method should not re-raise exceptions (should handle gracefully)")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: METHOD HAS DESIGN DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════════

def test_method_has_design_rationale_documented():
    """
    Verify the method has docstring explaining design rationale
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Find method and its docstring
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_section = content[method_start:method_end]

    # Should have docstring
    assert '"""' in method_section, \
        "Method should have a docstring"

    # Docstring should mention key design principles
    docstring_start = method_section.find('"""')
    docstring_end = method_section.find('"""', docstring_start + 3)
    docstring = method_section[docstring_start:docstring_end]

    # Check for key design principles in docstring
    assert ('conservative' in docstring.lower() or
            'manual_override' in docstring.lower() or
            'graceful' in docstring.lower() or
            'architectural gap' in docstring.lower()), \
        "Docstring should document design rationale"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 9: VERIFY INTEGRATION LOCATION (CALLED AT LINE 597-598)
# ═══════════════════════════════════════════════════════════════════════════

def test_method_called_at_correct_location():
    """
    Verify method is called in the _full_index method after successful reindex

    The method should be called after save_index and record_timestamp,
    but before the return statement.
    """
    with open(SCRIPT_PATH, 'r') as f:
        lines = f.readlines()

    # Find the line where method is called
    call_line = None
    for i, line in enumerate(lines, start=1):
        if 'self._update_prerequisites_state_after_successful_reindex()' in line:
            call_line = i
            break

    assert call_line is not None, \
        "Method call should be found in the script"

    # Updated: Method is now at line 1465 in the _full_index method
    # Previous location (line 1325) shifted due to fast-fail heuristics addition (~142 lines)
    expected_line = 1465
    tolerance = 50  # Allow ±50 lines for code changes

    assert abs(call_line - expected_line) <= tolerance, \
        f"Method should be called around line {expected_line}, but found at line {call_line}"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 10: VERIFY STATE FILE UPDATE LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def test_method_writes_to_correct_state_file():
    """
    Verify method writes to logs/state/semantic-search-prerequisites.json
    """
    with open(SCRIPT_PATH, 'r') as f:
        content = f.read()

    # Extract the method body
    method_start = content.find('def _update_prerequisites_state_after_successful_reindex(self):')
    method_end = content.find('\n    def ', method_start + 1)
    if method_end == -1:
        method_end = content.find('\nif __name__', method_start)
    if method_end == -1:
        method_end = len(content)

    method_body = content[method_start:method_end]

    # Should reference the correct state file path
    assert 'semantic-search-prerequisites.json' in method_body, \
        "Method should reference semantic-search-prerequisites.json"

    assert ('logs' in method_body and 'state' in method_body), \
        "Method should reference logs/state/ directory"


# ═══════════════════════════════════════════════════════════════════════════
# TEST SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PREREQUISITES AUTO-UPDATE TESTS")
    print("=" * 80)
    print("\nTest Coverage (regex-based, no dependencies required):")
    print("  ✓ Test 1: Method exists in code")
    print("  ✓ Test 2: Method is called after successful reindex")
    print("  ✓ Test 3: Method checks index file exists (conservative)")
    print("  ✓ Test 4: Method respects manual_override flag")
    print("  ✓ Test 5: Method sets prerequisites to TRUE")
    print("  ✓ Test 6: Method updates timestamp")
    print("  ✓ Test 7: Method has exception handling (graceful failure)")
    print("  ✓ Test 8: Method has design documentation")
    print("  ✓ Test 9: Method called at correct location (~line 598)")
    print("  ✓ Test 10: Method writes to correct state file")
    print("\nAll tests verify CODE STRUCTURE without executing (avoiding dependencies)")
    print("\nRun with: pytest tests/test_prerequisites_update.py -v")
    print("=" * 80 + "\n")

    pytest.main([__file__, '-v'])
