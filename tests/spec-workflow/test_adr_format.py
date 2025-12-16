#!/usr/bin/env python3
"""
Test Suite: ADR Format Validation
Layer 2 (Behavior) - Validates ADR files follow standard format

Purpose: Verify ADR files have required sections (Status, Context, Decision, etc.)
This is automatable because section headers are deterministic.

NOTE: This test should be run AFTER a skill execution to validate outputs.
      If no ADRs exist, tests will be skipped (not failed).

Run: python3 tests/spec-workflow/test_adr_format.py [project-slug]
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Required sections for a valid ADR
REQUIRED_SECTIONS = [
    "Status",
    "Context",
    "Decision",
]

# Recommended sections (warn if missing, don't fail)
RECOMMENDED_SECTIONS = [
    "Consequences",
    "Alternatives",
]

# Valid status values
VALID_STATUSES = [
    "Accepted",
    "Proposed",
    "Deprecated",
    "Superseded",
    "Draft",
    "Rejected",
]


class ADRTestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.warnings = 0
        self.failures: List[str] = []

    def pass_test(self, name: str):
        print(f"  [{GREEN}PASS{RESET}] {name}")
        self.passed += 1

    def fail_test(self, name: str, reason: str):
        print(f"  [{RED}FAIL{RESET}] {name}")
        self.failures.append(f"{name}: {reason}")
        self.failed += 1

    def skip_test(self, name: str, reason: str):
        print(f"  [{YELLOW}SKIP{RESET}] {name} - {reason}")
        self.skipped += 1

    def warn_test(self, name: str, reason: str):
        print(f"  [{YELLOW}WARN{RESET}] {name} - {reason}")
        self.warnings += 1


def find_project_dir(project_slug: Optional[str] = None) -> Optional[Path]:
    """Find the project directory to validate."""
    project_root = Path(__file__).parent.parent.parent

    if project_slug:
        # Check docs/projects first, then fixtures
        project_dir = project_root / "docs" / "projects" / project_slug
        if project_dir.exists():
            return project_dir
        fixture_dir = project_root / "tests" / "fixtures" / "generated" / project_slug
        if fixture_dir.exists():
            return fixture_dir
        return None

    # Find most recent project in either location
    all_project_dirs = []

    projects_dir = project_root / "docs" / "projects"
    if projects_dir.exists():
        all_project_dirs.extend([d for d in projects_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])

    fixtures_dir = project_root / "tests" / "fixtures" / "generated"
    if fixtures_dir.exists():
        all_project_dirs.extend([d for d in fixtures_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])

    if not all_project_dirs:
        return None

    # Return most recently modified
    return max(all_project_dirs, key=lambda d: d.stat().st_mtime)


def validate_adr(adr_path: Path) -> Tuple[bool, List[str], List[str]]:
    """
    Validate an ADR file has required sections.

    Returns: (is_valid, missing_required, missing_recommended)
    """
    content = adr_path.read_text()
    content_lower = content.lower()

    missing_required = []
    missing_recommended = []

    # Check required sections
    for section in REQUIRED_SECTIONS:
        # Look for ## Section or **Section** or # Section
        patterns = [
            f"## {section}".lower(),
            f"# {section}".lower(),
            f"**{section}**".lower(),
            f"### {section}".lower(),
        ]
        if not any(p in content_lower for p in patterns):
            missing_required.append(section)

    # Check recommended sections
    for section in RECOMMENDED_SECTIONS:
        patterns = [
            f"## {section}".lower(),
            f"# {section}".lower(),
            f"**{section}**".lower(),
            f"### {section}".lower(),
        ]
        if not any(p in content_lower for p in patterns):
            missing_recommended.append(section)

    is_valid = len(missing_required) == 0
    return is_valid, missing_required, missing_recommended


def validate_adr_status(adr_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if ADR has a valid status value."""
    content = adr_path.read_text()

    for status in VALID_STATUSES:
        if status.lower() in content.lower():
            return True, status

    return False, None


def section(title: str):
    print(f"\n{BLUE}=== {title} ==={RESET}")


def main():
    print(f"{BLUE}============================================{RESET}")
    print(f"{BLUE}  ADR Format Validation Test Suite{RESET}")
    print(f"{BLUE}============================================{RESET}")
    print()

    results = ADRTestResults()

    # Get project slug from argument
    project_slug = sys.argv[1] if len(sys.argv) > 1 else None

    # Find project directory
    project_dir = find_project_dir(project_slug)

    if not project_dir:
        print(f"{YELLOW}No project directory found.{RESET}")
        print("Usage: python3 tests/spec-workflow/test_adr_format.py [project-slug]")
        print()
        print("This test validates ADRs after skill execution.")
        print("Run the spec-workflow-orchestrator skill first to create outputs.")
        return 0

    print(f"Project: {project_dir.name}")
    print(f"Directory: {project_dir}")
    print()

    # Find ADR directory
    adr_dir = project_dir / "adrs"

    if not adr_dir.exists():
        print(f"{YELLOW}No ADR directory found at {adr_dir}{RESET}")
        print("Run the spec-workflow-orchestrator skill first to create ADRs.")
        return 0

    # Find ADR files
    adr_files = list(adr_dir.glob("ADR-*.md")) + list(adr_dir.glob("adr-*.md"))

    if not adr_files:
        print(f"{YELLOW}No ADR files found in {adr_dir}{RESET}")
        return 0

    # ============================================
    # SECTION 1: ADR Count
    # ============================================
    section("1. ADR Count")

    adr_count = len(adr_files)
    if 3 <= adr_count <= 7:
        results.pass_test(f"ADR count in expected range ({adr_count} ADRs)")
    elif adr_count > 0:
        if adr_count < 3:
            results.warn_test(f"ADR count", f"Only {adr_count} ADRs (expected 3-7)")
        else:
            results.pass_test(f"ADR count ({adr_count} ADRs - more than typical)")
    else:
        results.fail_test("ADR files exist", "No ADR files found")

    # ============================================
    # SECTION 2: Required Sections
    # ============================================
    section("2. Required Sections")

    for adr_path in adr_files:
        adr_name = adr_path.name
        is_valid, missing_required, missing_recommended = validate_adr(adr_path)

        if is_valid:
            results.pass_test(f"{adr_name} has required sections")
        else:
            results.fail_test(
                f"{adr_name} has required sections",
                f"Missing: {', '.join(missing_required)}"
            )

        # Warn about missing recommended sections
        if missing_recommended:
            results.warn_test(
                f"{adr_name} recommended sections",
                f"Missing: {', '.join(missing_recommended)}"
            )

    # ============================================
    # SECTION 3: Status Validation
    # ============================================
    section("3. Status Validation")

    for adr_path in adr_files:
        adr_name = adr_path.name
        has_status, status_value = validate_adr_status(adr_path)

        if has_status:
            results.pass_test(f"{adr_name} has valid status ({status_value})")
        else:
            results.warn_test(f"{adr_name} status", "No recognized status value found")

    # ============================================
    # SECTION 4: File Size Sanity Check
    # ============================================
    section("4. File Size Sanity Check")

    MIN_ADR_LINES = 20

    for adr_path in adr_files:
        adr_name = adr_path.name
        line_count = len(adr_path.read_text().splitlines())

        if line_count >= MIN_ADR_LINES:
            results.pass_test(f"{adr_name} has sufficient content ({line_count} lines)")
        else:
            results.warn_test(
                f"{adr_name} content size",
                f"Only {line_count} lines (expected {MIN_ADR_LINES}+)"
            )

    # ============================================
    # SUMMARY
    # ============================================
    print(f"\n{BLUE}============================================{RESET}")
    print(f"{BLUE}  SUMMARY{RESET}")
    print(f"{BLUE}============================================{RESET}")
    print()
    print(f"  {GREEN}Passed{RESET}: {results.passed}")
    print(f"  {RED}Failed{RESET}: {results.failed}")
    print(f"  {YELLOW}Warnings{RESET}: {results.warnings}")
    print(f"  {YELLOW}Skipped{RESET}: {results.skipped}")
    print()

    if results.failed > 0:
        print(f"{RED}FAILURES:{RESET}")
        for failure in results.failures:
            print(f"  - {failure}")
        print()
        print(f"{RED}Some tests FAILED. Review ADR format.{RESET}")
        return 1
    elif results.warnings > 0:
        print(f"{YELLOW}All required tests passed with {results.warnings} warnings.{RESET}")
        return 0
    else:
        print(f"{GREEN}All tests PASSED! ADR format is valid.{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
