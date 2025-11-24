#!/bin/bash
#
# Test Suite: Deliverable Structure Validation
# Layer 2 (Behavior) - Validates skill output files have required sections
#
# Purpose: After skill execution, verify output files have expected structure
# This is automatable because section headers are deterministic.
#
# NOTE: This test should be run AFTER a skill execution to validate outputs.
#       If no outputs exist, tests will be skipped (not failed).
#
# Run: ./tests/test_deliverable_structure.sh [project-slug]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Test result tracking
declare -a FAILURES

# Helper functions
pass() {
    echo -e "  [${GREEN}PASS${NC}] $1"
    ((PASSED++))
}

fail() {
    echo -e "  [${RED}FAIL${NC}] $1"
    FAILURES+=("$1: $2")
    ((FAILED++))
}

skip() {
    echo -e "  [${YELLOW}SKIP${NC}] $1 - $2"
    ((SKIPPED++))
}

section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Get project slug from argument or find most recent
PROJECT_SLUG="${1:-}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Deliverable Structure Validation${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Find project directory
if [ -n "$PROJECT_SLUG" ]; then
    PROJECT_DIR="docs/projects/$PROJECT_SLUG"
else
    # Find most recent project
    if [ -d "docs/projects" ]; then
        PROJECT_DIR=$(ls -td docs/projects/*/ 2>/dev/null | head -1 | sed 's:/$::')
        if [ -n "$PROJECT_DIR" ]; then
            PROJECT_SLUG=$(basename "$PROJECT_DIR")
        fi
    fi
fi

if [ -z "$PROJECT_DIR" ] || [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}No project directory found.${NC}"
    echo "Usage: $0 [project-slug]"
    echo ""
    echo "This test validates deliverables after skill execution."
    echo "Run the spec-workflow-orchestrator skill first to create outputs."
    exit 0
fi

echo "Project: $PROJECT_SLUG"
echo "Directory: $PROJECT_DIR"
echo ""

# ============================================
# SECTION 1: Planning Files Exist
# ============================================
section "1. Planning Files Exist"

REQUIREMENTS_FILE="$PROJECT_DIR/planning/requirements.md"
ARCHITECTURE_FILE="$PROJECT_DIR/planning/architecture.md"
TASKS_FILE="$PROJECT_DIR/planning/tasks.md"

if [ -f "$REQUIREMENTS_FILE" ]; then
    pass "requirements.md exists"
else
    skip "requirements.md exists" "File not found (run skill first)"
fi

if [ -f "$ARCHITECTURE_FILE" ]; then
    pass "architecture.md exists"
else
    skip "architecture.md exists" "File not found (run skill first)"
fi

if [ -f "$TASKS_FILE" ]; then
    pass "tasks.md exists"
else
    skip "tasks.md exists" "File not found (run skill first)"
fi

# ============================================
# SECTION 2: Requirements Structure
# ============================================
section "2. Requirements Structure"

if [ -f "$REQUIREMENTS_FILE" ]; then
    # Check for Functional Requirements section
    if grep -qi "## Functional Requirements\|## FRs\|### FR-" "$REQUIREMENTS_FILE"; then
        pass "requirements.md has Functional Requirements section"
    else
        fail "requirements.md has Functional Requirements section" "Section not found"
    fi

    # Check for Non-Functional Requirements section
    if grep -qi "## Non-Functional Requirements\|## NFRs\|### NFR-" "$REQUIREMENTS_FILE"; then
        pass "requirements.md has Non-Functional Requirements section"
    else
        fail "requirements.md has Non-Functional Requirements section" "Section not found"
    fi

    # Check for User Stories section
    if grep -qi "## User Stories\|### US-\|As a.*I want" "$REQUIREMENTS_FILE"; then
        pass "requirements.md has User Stories"
    else
        fail "requirements.md has User Stories" "User stories not found"
    fi

    # Check for Stakeholders section
    if grep -qi "## Stakeholder\|stakeholder" "$REQUIREMENTS_FILE"; then
        pass "requirements.md mentions stakeholders"
    else
        skip "requirements.md mentions stakeholders" "Section not found"
    fi
else
    skip "Requirements structure validation" "File does not exist"
fi

# ============================================
# SECTION 3: Architecture Structure
# ============================================
section "3. Architecture Structure"

if [ -f "$ARCHITECTURE_FILE" ]; then
    # Check for Technology Stack section
    if grep -qi "## Technology Stack\|## Tech Stack\|### Technologies" "$ARCHITECTURE_FILE"; then
        pass "architecture.md has Technology Stack section"
    else
        fail "architecture.md has Technology Stack section" "Section not found"
    fi

    # Check for Components section
    if grep -qi "## Components\|## System Components\|## Architecture" "$ARCHITECTURE_FILE"; then
        pass "architecture.md has Components section"
    else
        fail "architecture.md has Components section" "Section not found"
    fi

    # Check for API section (optional but common)
    if grep -qi "## API\|### Endpoints\|REST\|GraphQL" "$ARCHITECTURE_FILE"; then
        pass "architecture.md has API specifications"
    else
        skip "architecture.md has API specifications" "Section not found"
    fi

    # Check for Security section
    if grep -qi "## Security\|security" "$ARCHITECTURE_FILE"; then
        pass "architecture.md mentions security"
    else
        skip "architecture.md mentions security" "Section not found"
    fi
else
    skip "Architecture structure validation" "File does not exist"
fi

# ============================================
# SECTION 4: Tasks Structure
# ============================================
section "4. Tasks Structure"

if [ -f "$TASKS_FILE" ]; then
    # Check for Phase sections
    if grep -qi "## Phase\|### Phase" "$TASKS_FILE"; then
        pass "tasks.md has Phase sections"
    else
        fail "tasks.md has Phase sections" "Phase sections not found"
    fi

    # Check for task IDs
    if grep -qE "TASK-[0-9]+|T-[0-9]+|\*\*[0-9]+\." "$TASKS_FILE"; then
        pass "tasks.md has task identifiers"
    else
        skip "tasks.md has task identifiers" "Task IDs not found (may use different format)"
    fi

    # Check for dependencies mentioned
    if grep -qi "dependenc\|depends on\|blocked by\|prerequisite" "$TASKS_FILE"; then
        pass "tasks.md mentions dependencies"
    else
        skip "tasks.md mentions dependencies" "Dependencies not explicitly mentioned"
    fi

    # Check for estimates
    if grep -qi "hour\|day\|estimate\|effort\|complexity" "$TASKS_FILE"; then
        pass "tasks.md has effort estimates"
    else
        skip "tasks.md has effort estimates" "Estimates not found"
    fi

    # Check for risk section
    if grep -qi "## Risk\|### Risk\|risk" "$TASKS_FILE"; then
        pass "tasks.md mentions risks"
    else
        skip "tasks.md mentions risks" "Risk section not found"
    fi
else
    skip "Tasks structure validation" "File does not exist"
fi

# ============================================
# SECTION 5: ADR Files
# ============================================
section "5. ADR Files"

ADR_DIR="$PROJECT_DIR/adrs"

if [ -d "$ADR_DIR" ]; then
    ADR_COUNT=$(ls "$ADR_DIR"/ADR-*.md 2>/dev/null | wc -l | tr -d ' ')

    if [ "$ADR_COUNT" -ge 3 ] && [ "$ADR_COUNT" -le 7 ]; then
        pass "ADR count in range ($ADR_COUNT ADRs, expected 3-7)"
    elif [ "$ADR_COUNT" -gt 0 ]; then
        if [ "$ADR_COUNT" -lt 3 ]; then
            fail "ADR count in range" "Only $ADR_COUNT ADRs (expected 3-7)"
        else
            pass "ADR count ($ADR_COUNT ADRs - more than typical but acceptable)"
        fi
    else
        fail "ADR files exist" "No ADR files found in $ADR_DIR"
    fi
else
    skip "ADR validation" "ADR directory does not exist"
fi

# ============================================
# SECTION 6: File Sizes (Sanity Check)
# ============================================
section "6. File Size Sanity Check"

MIN_REQUIREMENTS_LINES=100
MIN_ARCHITECTURE_LINES=100
MIN_TASKS_LINES=50

if [ -f "$REQUIREMENTS_FILE" ]; then
    LINES=$(wc -l < "$REQUIREMENTS_FILE" | tr -d ' ')
    if [ "$LINES" -ge "$MIN_REQUIREMENTS_LINES" ]; then
        pass "requirements.md has sufficient content ($LINES lines)"
    else
        fail "requirements.md has sufficient content" "Only $LINES lines (expected $MIN_REQUIREMENTS_LINES+)"
    fi
fi

if [ -f "$ARCHITECTURE_FILE" ]; then
    LINES=$(wc -l < "$ARCHITECTURE_FILE" | tr -d ' ')
    if [ "$LINES" -ge "$MIN_ARCHITECTURE_LINES" ]; then
        pass "architecture.md has sufficient content ($LINES lines)"
    else
        fail "architecture.md has sufficient content" "Only $LINES lines (expected $MIN_ARCHITECTURE_LINES+)"
    fi
fi

if [ -f "$TASKS_FILE" ]; then
    LINES=$(wc -l < "$TASKS_FILE" | tr -d ' ')
    if [ "$LINES" -ge "$MIN_TASKS_LINES" ]; then
        pass "tasks.md has sufficient content ($LINES lines)"
    else
        fail "tasks.md has sufficient content" "Only $LINES lines (expected $MIN_TASKS_LINES+)"
    fi
fi

# ============================================
# SUMMARY
# ============================================
echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}  SUMMARY${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "  ${GREEN}Passed${NC}: $PASSED"
echo -e "  ${RED}Failed${NC}: $FAILED"
echo -e "  ${YELLOW}Skipped${NC}: $SKIPPED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}FAILURES:${NC}"
    for failure in "${FAILURES[@]}"; do
        echo -e "  - $failure"
    done
    echo ""
    echo -e "${RED}Some tests FAILED. Review deliverable structure.${NC}"
    exit 1
elif [ $SKIPPED -gt 0 ] && [ $PASSED -eq 0 ]; then
    echo -e "${YELLOW}All tests skipped. Run skill first to create deliverables.${NC}"
    exit 0
else
    echo -e "${GREEN}All tests PASSED! Deliverable structure is valid.${NC}"
    exit 0
fi
