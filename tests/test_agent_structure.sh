#!/bin/bash
#
# Test Suite: Agent Structure Validation
# Layer 2 (Behavior) - Validates agents exist and have required structure
#
# Purpose: Verify agent files exist at expected paths with valid frontmatter
# This is automatable because file existence is deterministic.
#
# Run: ./tests/test_agent_structure.sh
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
    PASSED=$((PASSED + 1))
}

fail() {
    echo -e "  [${RED}FAIL${NC}] $1"
    FAILURES+=("$1: $2")
    FAILED=$((FAILED + 1))
}

skip() {
    echo -e "  [${YELLOW}SKIP${NC}] $1 - $2"
    SKIPPED=$((SKIPPED + 1))
}

section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Agent Structure Validation Test Suite${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# ============================================
# SECTION 1: Planning Agents Exist
# ============================================
section "1. Planning Agents Exist"

# Test: spec-analyst agent exists
if [ -f ".claude/agents/spec-analyst.md" ]; then
    pass "spec-analyst.md exists"
else
    fail "spec-analyst.md exists" "File not found at .claude/agents/spec-analyst.md"
fi

# Test: spec-architect agent exists
if [ -f ".claude/agents/spec-architect.md" ]; then
    pass "spec-architect.md exists"
else
    fail "spec-architect.md exists" "File not found at .claude/agents/spec-architect.md"
fi

# Test: spec-planner agent exists
if [ -f ".claude/agents/spec-planner.md" ]; then
    pass "spec-planner.md exists"
else
    fail "spec-planner.md exists" "File not found at .claude/agents/spec-planner.md"
fi

# ============================================
# SECTION 2: Research Agents Exist
# ============================================
section "2. Research Agents Exist"

# Test: researcher agent exists
if [ -f ".claude/agents/researcher.md" ]; then
    pass "researcher.md exists"
else
    fail "researcher.md exists" "File not found at .claude/agents/researcher.md"
fi

# Test: report-writer agent exists
if [ -f ".claude/agents/report-writer.md" ]; then
    pass "report-writer.md exists"
else
    fail "report-writer.md exists" "File not found at .claude/agents/report-writer.md"
fi

# ============================================
# SECTION 3: Agent Frontmatter Validation
# ============================================
section "3. Agent Frontmatter Validation"

# Function to check frontmatter field exists
check_frontmatter() {
    local file=$1
    local field=$2
    local agent_name=$(basename "$file" .md)

    if grep -q "^${field}:" "$file" 2>/dev/null; then
        pass "$agent_name has '$field' frontmatter"
        return 0
    else
        fail "$agent_name has '$field' frontmatter" "Field not found in $file"
        return 1
    fi
}

# Check all planning agents have required frontmatter
for agent in .claude/agents/spec-*.md; do
    if [ -f "$agent" ]; then
        check_frontmatter "$agent" "tools"
    fi
done

# Check research agents have required frontmatter
for agent in .claude/agents/researcher.md .claude/agents/report-writer.md; do
    if [ -f "$agent" ]; then
        check_frontmatter "$agent" "tools"
    fi
done

# ============================================
# SECTION 4: Skill Files Exist
# ============================================
section "4. Skill Files Exist"

# Test: multi-agent-researcher skill exists
if [ -f ".claude/skills/multi-agent-researcher/SKILL.md" ]; then
    pass "multi-agent-researcher SKILL.md exists"
else
    fail "multi-agent-researcher SKILL.md exists" "File not found"
fi

# Test: spec-workflow-orchestrator skill exists
if [ -f ".claude/skills/spec-workflow-orchestrator/SKILL.md" ]; then
    pass "spec-workflow-orchestrator SKILL.md exists"
else
    fail "spec-workflow-orchestrator SKILL.md exists" "File not found"
fi

# ============================================
# SECTION 5: Configuration Files Exist
# ============================================
section "5. Configuration Files Exist"

# Test: skill-rules.json exists
if [ -f ".claude/skills/skill-rules.json" ]; then
    pass "skill-rules.json exists"
else
    fail "skill-rules.json exists" "File not found"
fi

# Test: skill-rules.json is valid JSON
if [ -f ".claude/skills/skill-rules.json" ]; then
    if python3 -c "import json; json.load(open('.claude/skills/skill-rules.json'))" 2>/dev/null; then
        pass "skill-rules.json is valid JSON"
    else
        fail "skill-rules.json is valid JSON" "JSON parse error"
    fi
fi

# Test: CLAUDE.md exists
if [ -f ".claude/CLAUDE.md" ]; then
    pass "CLAUDE.md exists"
else
    fail "CLAUDE.md exists" "File not found"
fi

# ============================================
# SECTION 6: Hook Files Exist
# ============================================
section "6. Hook Files Exist"

# Test: user-prompt-submit hook exists
if [ -f ".claude/hooks/user-prompt-submit.py" ]; then
    pass "user-prompt-submit.py exists"
else
    fail "user-prompt-submit.py exists" "File not found"
fi

# Test: hook is executable or has python shebang
if [ -f ".claude/hooks/user-prompt-submit.py" ]; then
    if head -1 .claude/hooks/user-prompt-submit.py | grep -q "python"; then
        pass "user-prompt-submit.py has Python shebang"
    elif [ -x ".claude/hooks/user-prompt-submit.py" ]; then
        pass "user-prompt-submit.py is executable"
    else
        skip "user-prompt-submit.py shebang/executable check"
    fi
fi

# ============================================
# SECTION 7: Utility Scripts Exist
# ============================================
section "7. Utility Scripts Exist"

UTILS=("archive_project.sh" "restore_archive.sh" "list_archives.sh" "workflow_state.sh" "detect_next_version.sh")

for util in "${UTILS[@]}"; do
    if [ -f ".claude/utils/$util" ]; then
        pass "$util exists"
    else
        fail "$util exists" "File not found at .claude/utils/$util"
    fi
done

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
    echo -e "${RED}Some tests FAILED. Review agent structure.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests PASSED! Agent structure is valid.${NC}"
    exit 0
fi
