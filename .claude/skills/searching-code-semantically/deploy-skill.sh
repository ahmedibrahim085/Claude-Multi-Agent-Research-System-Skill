#!/usr/bin/env bash
#===============================================================================
# Deploy searching-code-semantically Skill
#===============================================================================
#
# Purpose: Clean deployment of skill to ~/.claude/skills/
#
# This script ensures ONLY production files are deployed, excluding:
# - Development artifacts (logs/, tests/, .benchmarks/)
# - Git metadata (.gitignore)
# - Python cache (__pycache__, *.pyc)
#
# Per official Anthropic skill structure requirements:
# https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
#
#===============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="searching-code-semantically"
SOURCE_DIR="$SCRIPT_DIR"
TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Deploying Skill: $SKILL_NAME${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Verify source files exist
echo -e "${YELLOW}Step 1: Verifying source files...${NC}"
if [ ! -f "$SOURCE_DIR/SKILL.md" ]; then
    echo -e "${RED}ERROR: SKILL.md not found in $SOURCE_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SKILL.md found${NC}"

# Step 2: Create target directory
echo -e "\n${YELLOW}Step 2: Preparing target directory...${NC}"
mkdir -p "$TARGET_DIR"
echo -e "${GREEN}✓ Target directory: $TARGET_DIR${NC}"

# Step 3: Clean existing deployment (remove artifacts)
echo -e "\n${YELLOW}Step 3: Cleaning existing deployment...${NC}"
if [ -d "$TARGET_DIR" ]; then
    # Remove development artifacts
    rm -rf "$TARGET_DIR/logs" 2>/dev/null || true
    rm -rf "$TARGET_DIR/tests" 2>/dev/null || true
    rm -rf "$TARGET_DIR/.benchmarks" 2>/dev/null || true
    rm -rf "$TARGET_DIR/__pycache__" 2>/dev/null || true
    rm -rf "$TARGET_DIR/scripts/__pycache__" 2>/dev/null || true
    rm -f "$TARGET_DIR/.gitignore" 2>/dev/null || true
    find "$TARGET_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$TARGET_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}✓ Removed development artifacts${NC}"
fi

# Step 4: Deploy production files
echo -e "\n${YELLOW}Step 4: Deploying production files...${NC}"

# Copy SKILL.md (required)
cp "$SOURCE_DIR/SKILL.md" "$TARGET_DIR/"
echo -e "${GREEN}✓ SKILL.md${NC}"

# Copy references/ directory
if [ -d "$SOURCE_DIR/references" ]; then
    cp -r "$SOURCE_DIR/references" "$TARGET_DIR/"
    echo -e "${GREEN}✓ references/ ($(ls -1 $SOURCE_DIR/references/*.md | wc -l | tr -d ' ') files)${NC}"
fi

# Copy scripts/ directory (excluding __pycache__)
if [ -d "$SOURCE_DIR/scripts" ]; then
    mkdir -p "$TARGET_DIR/scripts"
    # Copy only .py files
    cp "$SOURCE_DIR/scripts"/*.py "$TARGET_DIR/scripts/" 2>/dev/null || true
    chmod +x "$TARGET_DIR/scripts"/*.py 2>/dev/null || true
    echo -e "${GREEN}✓ scripts/ ($(ls -1 $TARGET_DIR/scripts/*.py | wc -l | tr -d ' ') files)${NC}"
fi

# README.md intentionally excluded per skill-creator best practices
# Official guidance: "Do NOT create extraneous documentation or auxiliary files, including: README.md"
# Essential API stability content has been moved to references/api-stability.md
echo -e "${GREEN}✓ README.md excluded (per skill-creator guidelines)${NC}"

# Step 5: Verify deployment
echo -e "\n${YELLOW}Step 5: Verifying deployment...${NC}"
echo ""
echo "Deployed files:"
find "$TARGET_DIR" -type f | sort | while read file; do
    rel_path="${file#$TARGET_DIR/}"
    file_size=$(ls -lh "$file" | awk '{print $5}')
    echo "  $rel_path ($file_size)"
done

# Step 6: Verify frontmatter compliance
echo -e "\n${YELLOW}Step 6: Checking SKILL.md frontmatter compliance...${NC}"
if grep -q "^name: $SKILL_NAME" "$TARGET_DIR/SKILL.md"; then
    echo -e "${GREEN}✓ 'name' field present${NC}"
else
    echo -e "${RED}✗ 'name' field MISSING${NC}"
    exit 1
fi

if grep -q "^description:" "$TARGET_DIR/SKILL.md"; then
    echo -e "${GREEN}✓ 'description' field present${NC}"
else
    echo -e "${RED}✗ 'description' field MISSING${NC}"
    exit 1
fi

if grep -q "^allowed-tools:" "$TARGET_DIR/SKILL.md"; then
    echo -e "${RED}✗ FORBIDDEN 'allowed-tools' field found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No forbidden fields${NC}"
fi

# Step 7: Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Skill location: $TARGET_DIR"
echo ""
echo "Usage:"
echo "  Manual: /skill $SKILL_NAME"
echo "  Auto: Triggers on 'how does X work', 'find code that does Y'"
echo ""
echo "Verification:"
echo "  ls -la $TARGET_DIR"
echo ""
