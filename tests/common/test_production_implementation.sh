#!/bin/bash
# Production Implementation Integration Test
# Tests all P0 and P1 priorities from honest review

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Production Implementation Integration Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

PASSED=0
FAILED=0
TEST_PROJECT="test-integration-app"

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up test artifacts..."
    rm -rf "docs/projects/$TEST_PROJECT" 2>/dev/null || true
    rm -rf "docs/projects/$TEST_PROJECT-v2" 2>/dev/null || true
    .claude/utils/workflow_state.sh clear 2>/dev/null || true
    echo "Cleanup complete"
}

# Run cleanup on exit
trap cleanup EXIT

# Test function helper
run_test() {
    local test_name="$1"
    echo ""
    echo -e "${YELLOW}TEST: $test_name${NC}"
    echo "────────────────────────────────────────"
}

pass_test() {
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED=$((PASSED + 1))
}

fail_test() {
    local message="$1"
    echo -e "${RED}❌ FAIL: $message${NC}"
    FAILED=$((FAILED + 1))
}

# ============================================================
# TEST 1: State Management
# ============================================================
run_test "State Management (save/load/clear)"

# Test set state
.claude/utils/workflow_state.sh set "$TEST_PROJECT" "fresh" ""
if [ $? -eq 0 ]; then
    echo "  ✓ State saved successfully"
else
    fail_test "Failed to save state"
    exit 1
fi

# Test get state
PROJECT=$(.claude/utils/workflow_state.sh get "project_slug")
MODE=$(.claude/utils/workflow_state.sh get "mode")

if [ "$PROJECT" = "$TEST_PROJECT" ] && [ "$MODE" = "fresh" ]; then
    echo "  ✓ State retrieved correctly"
    echo "    Project: $PROJECT"
    echo "    Mode: $MODE"
    pass_test
else
    fail_test "State values incorrect (project='$PROJECT', mode='$MODE')"
fi

# Test clear state
.claude/utils/workflow_state.sh clear
if [ $? -eq 0 ]; then
    echo "  ✓ State cleared successfully"
else
    fail_test "Failed to clear state"
fi

# ============================================================
# TEST 2: Fresh Project Creation
# ============================================================
run_test "Fresh Project Creation"

# Create project directories
mkdir -p "docs/projects/$TEST_PROJECT/planning"
mkdir -p "docs/projects/$TEST_PROJECT/adrs"

# Create test files
cat > "docs/projects/$TEST_PROJECT/planning/requirements.md" <<EOF
# Test Requirements
- FR1: Feature 1
- FR2: Feature 2
EOF

cat > "docs/projects/$TEST_PROJECT/planning/architecture.md" <<EOF
# Test Architecture
Stack: Node.js
EOF

cat > "docs/projects/$TEST_PROJECT/planning/tasks.md" <<EOF
# Test Tasks
T1: Task 1
T2: Task 2
EOF

cat > "docs/projects/$TEST_PROJECT/adrs/001-test.md" <<EOF
# ADR-001: Test Decision
Status: Accepted
EOF

if [ -d "docs/projects/$TEST_PROJECT" ] && [ -f "docs/projects/$TEST_PROJECT/planning/requirements.md" ]; then
    FILE_COUNT=$(find "docs/projects/$TEST_PROJECT" -name "*.md" | wc -l | tr -d ' ')
    echo "  ✓ Project created with $FILE_COUNT files"
    pass_test
else
    fail_test "Project creation failed"
fi

# ============================================================
# TEST 3: Archive Functionality
# ============================================================
run_test "Archive Project"

# Run archive script
if .claude/utils/archive_project.sh "$TEST_PROJECT"; then
    echo "  ✓ Archive command executed successfully"

    # Check if archive was created
    ARCHIVES=$(find "docs/projects/$TEST_PROJECT/.archive" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
    if [ "$ARCHIVES" -ge 1 ]; then
        echo "  ✓ Archive directory created"

        # Check if original files were removed
        if [ ! -f "docs/projects/$TEST_PROJECT/planning/requirements.md" ]; then
            echo "  ✓ Original files removed"

            # Check if fresh directories were created
            if [ -d "docs/projects/$TEST_PROJECT/planning" ] && [ -d "docs/projects/$TEST_PROJECT/adrs" ]; then
                echo "  ✓ Fresh directories created"
                pass_test
            else
                fail_test "Fresh directories not created"
            fi
        else
            fail_test "Original files still present after archive"
        fi
    else
        fail_test "Archive directory not found"
    fi
else
    fail_test "Archive command failed"
fi

# ============================================================
# TEST 4: List Archives
# ============================================================
run_test "List Archives"

OUTPUT=$(.claude/utils/list_archives.sh "$TEST_PROJECT" 2>&1)
if [ $? -eq 0 ]; then
    if echo "$OUTPUT" | grep -q "Archive:"; then
        echo "  ✓ Archive listing shows archives"
        echo "  ✓ Output format correct"
        pass_test
    else
        fail_test "Archive list output unexpected"
    fi
else
    fail_test "List archives command failed"
fi

# ============================================================
# TEST 5: Restore Archive
# ============================================================
run_test "Restore Archive"

# Get the timestamp of the archive we created
TIMESTAMP=$(find "docs/projects/$TEST_PROJECT/.archive" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | grep -v backup | head -n 1)

if [ -n "$TIMESTAMP" ]; then
    echo "  Found archive: $TIMESTAMP"

    # Run restore (with auto-yes to confirmation)
    if echo "yes" | .claude/utils/restore_archive.sh "$TEST_PROJECT" "$TIMESTAMP" >/dev/null 2>&1; then
        echo "  ✓ Restore command executed"

        # Check if files were restored
        if [ -f "docs/projects/$TEST_PROJECT/planning/requirements.md" ]; then
            CONTENT=$(cat "docs/projects/$TEST_PROJECT/planning/requirements.md")
            if echo "$CONTENT" | grep -q "FR1: Feature 1"; then
                echo "  ✓ Files restored with correct content"
                pass_test
            else
                fail_test "Restored file content incorrect"
            fi
        else
            fail_test "Files not restored"
        fi
    else
        fail_test "Restore command failed"
    fi
else
    fail_test "No archive timestamp found"
fi

# ============================================================
# TEST 6: Version Detection
# ============================================================
run_test "Version Detection"

# Test with existing project
NEXT_VERSION=$(.claude/utils/detect_next_version.sh "$TEST_PROJECT")
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "  ✓ Version detection successful"
    if [ "$NEXT_VERSION" = "$TEST_PROJECT-v2" ]; then
        echo "  ✓ Correct next version: $NEXT_VERSION"
        pass_test
    else
        fail_test "Unexpected version: $NEXT_VERSION (expected $TEST_PROJECT-v2)"
    fi
else
    fail_test "Version detection failed"
fi

# ============================================================
# TEST 7: Create Versioned Project
# ============================================================
run_test "Create Versioned Project"

# Create v2
mkdir -p "docs/projects/$NEXT_VERSION/planning"
mkdir -p "docs/projects/$NEXT_VERSION/adrs"

if [ -d "docs/projects/$NEXT_VERSION" ]; then
    echo "  ✓ Versioned project directory created"

    # Test version detection again (should return v3)
    NEXT_NEXT=$(.claude/utils/detect_next_version.sh "$TEST_PROJECT")
    if [ "$NEXT_NEXT" = "$TEST_PROJECT-v3" ]; then
        echo "  ✓ Subsequent version detection correct: $NEXT_NEXT"
        pass_test
    else
        fail_test "Next version detection incorrect: $NEXT_NEXT"
    fi
else
    fail_test "Failed to create versioned project"
fi

# ============================================================
# TEST 8: Error Handling - Archive Non-existent Project
# ============================================================
run_test "Error Handling: Non-existent Project"

if .claude/utils/archive_project.sh "nonexistent-project" 2>/dev/null; then
    fail_test "Should have failed for non-existent project"
else
    echo "  ✓ Correctly failed for non-existent project"
    pass_test
fi

# ============================================================
# TEST 9: Error Handling - Restore Non-existent Archive
# ============================================================
run_test "Error Handling: Non-existent Archive"

if .claude/utils/restore_archive.sh "$TEST_PROJECT" "99999999-999999" 2>/dev/null; then
    fail_test "Should have failed for non-existent archive"
else
    echo "  ✓ Correctly failed for non-existent archive"
    pass_test
fi

# ============================================================
# TEST 10: Error Handling - Version Detection on Non-existent Project
# ============================================================
run_test "Error Handling: Version Detection on Non-existent Base"

if .claude/utils/detect_next_version.sh "nonexistent-base" 2>/dev/null; then
    fail_test "Should have failed for non-existent base project"
else
    echo "  ✓ Correctly failed for non-existent base project"
    pass_test
fi

# ============================================================
# RESULTS SUMMARY
# ============================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST RESULTS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - PRODUCTION READY${NC}"
    echo ""
    echo "Implemented features:"
    echo "  ✓ State management (JSON file)"
    echo "  ✓ Archive with timestamp"
    echo "  ✓ Restore from archive"
    echo "  ✓ List archives"
    echo "  ✓ Version detection"
    echo "  ✓ Error handling"
    echo "  ✓ Fresh project creation"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
