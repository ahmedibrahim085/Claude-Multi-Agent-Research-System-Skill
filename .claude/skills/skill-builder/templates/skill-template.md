---
name: your-skill-name
description: Use this skill when [describe specific situations when this skill should be invoked]. This includes [list concrete use cases and trigger keywords that should activate this skill].
---

# [Skill Name]

[Brief overview of what this skill does and why it exists - keep concise]

# Core Approach

[Describe the fundamental methodology this skill uses]

# Step-by-Step Instructions

## 1. [First Major Step]

[Clear, actionable instructions for the first step]

- Specific action using CLI tools where applicable
- Another action item
- Validation step

**CLI Tools:**
- `command-name` - What it does
- `another-command` - What it does

## 2. [Second Major Step]

[Clear, actionable instructions]

**Node.js Example:**
```javascript
#!/usr/bin/env node
import { readFile } from 'fs/promises';

// Your implementation here
const data = await readFile('input.txt', 'utf-8');
console.log(data);
```

## 3. [Third Major Step]

[Clear, actionable instructions with complete, runnable commands]

```bash
gh repo view --json name,description
npm install -g useful-package
aws s3 ls s3://bucket-name/
```

# Examples

## Example 1: [Use Case Name]

**User Query**: "[Example of what user might say]"

**Approach**:
1. Use `cli-tool` to gather information
2. Process with Node.js script
3. Validate output with another CLI command

**Complete Commands:**
```bash
# Step 1
gh api repos/owner/repo

# Step 2 - Node.js processing
node process-data.js

# Step 3 - Validation
npm test
```

**Expected Outcome**: [What should result]

## Example 2: [Another Use Case]

**User Query**: "[Another example query]"

**Approach**:
1. [Step using CLI tools]
2. [Step using Node.js]
3. [Verification step]

# CLI Tools to Leverage

**Essential tools for this skill:**
- `gh` - GitHub CLI operations
- `npm` - Package management and script running
- `aws` - AWS CLI operations (if applicable)
- `git` - Version control operations
- `jq` - JSON processing
- [Other relevant CLI tools]

**Global NPM Packages to Consider:**
- `npm install -g package-name` - [Purpose]
- `npm install -g another-package` - [Purpose]

# Node.js Patterns

**File Operations:**
```javascript
#!/usr/bin/env node
import { readFile, writeFile } from 'fs/promises';

const content = await readFile('input.txt', 'utf-8');
await writeFile('output.txt', content.toUpperCase());
```

**Running CLI Commands from Node:**
```javascript
#!/usr/bin/env node
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const { stdout } = await execAsync('gh repo view --json name');
const repo = JSON.parse(stdout);
console.log(repo.name);
```

**Processing JSON Data:**
```javascript
#!/usr/bin/env node
import { readFile } from 'fs/promises';

const data = JSON.parse(await readFile('data.json', 'utf-8'));
const filtered = data.filter(item => item.active);
console.log(filtered);
```

# Best Practices

- Challenge each instruction: "Does Claude really need this context?"
- Keep SKILL.md under 500 lines
- Use CLI tools liberally for operations
- Write Node.js scripts (not Python) for complex logic
- Provide complete, runnable commands
- Reference supporting files with relative paths (e.g., `./details.md`)
- Use intention-revealing names for all files
- Show command chaining when helpful

# Validation Checklist

When completing a task with this skill, verify:
- [ ] CLI commands executed successfully
- [ ] Output matches expected format
- [ ] No errors in console output
- [ ] Results are validated with test commands
- [ ] [Domain-specific validation item]

# Troubleshooting

## Issue: [Common Problem]

**Symptoms**: [What user sees]

**Investigation**:
```bash
# Check logs or status
command-to-diagnose
```

**Solution**: [How to fix with specific commands]

## Issue: [Another Problem]

**Symptoms**: [What user sees]

**Investigation**:
```bash
# Diagnostic command
another-diagnostic-command
```

**Solution**: [How to fix]

# Supporting Files

[Reference other files in the skill directory using relative paths]

- See `./detailed-methodology.md` for [what it contains]
- See `./templates/` for [what templates are available]
- See `./scripts/` for [what helper scripts exist]

Remember: All scripts should be Node.js with ESM imports, not Python!
