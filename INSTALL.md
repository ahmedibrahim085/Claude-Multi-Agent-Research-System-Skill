# Installation Guide

Complete step-by-step installation instructions for the Multi-Agent Research plugin.

---

## Step 1: Get API Keys

### Exa API Key
1. Visit https://dashboard.exa.ai/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create API Key**
5. Copy the key (starts with `exa_...`)

### Tavily API Key
1. Visit https://app.tavily.com/
2. Sign up or log in
3. Go to **Settings** → **API**
4. Copy your API key

### Brave Search API Key
1. Visit https://brave.com/search/api/
2. Request API access
3. Complete registration
4. Copy API key from dashboard

### Perplexity API Key
1. Visit https://www.perplexity.ai/settings/api
2. Log in to your account
3. Click **Generate API Key**
4. Copy the key

---

## Step 2: Set Environment Variables

### Windows (PowerShell)

**Temporary** (current session only):
```powershell
$env:EXA_API_KEY="your-exa-key"
$env:TAVILY_API_KEY="your-tavily-key"
$env:BRAVE_API_KEY="your-brave-key"
$env:PERPLEXITY_API_KEY="your-perplexity-key"
```

**Permanent** (recommended):
```powershell
[System.Environment]::SetEnvironmentVariable("EXA_API_KEY", "your-exa-key", "User")
[System.Environment]::SetEnvironmentVariable("TAVILY_API_KEY", "your-tavily-key", "User")
[System.Environment]::SetEnvironmentVariable("BRAVE_API_KEY", "your-brave-key", "User")
[System.Environment]::SetEnvironmentVariable("PERPLEXITY_API_KEY", "your-perplexity-key", "User")
```

**Verify**:
```powershell
echo $env:EXA_API_KEY
```

### macOS/Linux (Bash/Zsh)

**Temporary**:
```bash
export EXA_API_KEY="your-exa-key"
export TAVILY_API_KEY="your-tavily-key"
export BRAVE_API_KEY="your-brave-key"
export PERPLEXITY_API_KEY="your-perplexity-key"
```

**Permanent**:
```bash
echo 'export EXA_API_KEY="your-exa-key"' >> ~/.bashrc
echo 'export TAVILY_API_KEY="your-tavily-key"' >> ~/.bashrc
echo 'export BRAVE_API_KEY="your-brave-key"' >> ~/.bashrc
echo 'export PERPLEXITY_API_KEY="your-perplexity-key"' >> ~/.bashrc

# Apply changes
source ~/.bashrc
```

**Verify**:
```bash
echo $EXA_API_KEY
```

---

## Step 3: Install Plugin

### Option A: From Git Repository

```bash
# Clone repository
git clone <repo-url> multi-agent-researcher
cd multi-agent-researcher

# Verify files
ls -la
# Should see: .claude-plugin/, agents/, commands/, skills/, .mcp.json, hooks/
```

### Option B: Download ZIP

1. Download from releases page
2. Extract to desired location
3. Navigate to extracted directory

---

## Step 4: Create Development Marketplace

```bash
# Go to parent directory
cd ..

# Create marketplace directory
mkdir dev-marketplace
cd dev-marketplace

# Create marketplace manifest
mkdir .claude-plugin
```

**Windows (PowerShell)**:
```powershell
@"
{
  "name": "dev-marketplace",
  "owner": {"name": "Developer"},
  "plugins": [{
    "name": "multi-agent-researcher",
    "source": "../multi-agent-researcher",
    "description": "Multi-agent research with MCP search"
  }]
}
"@ | Out-File -FilePath .claude-plugin/marketplace.json -Encoding UTF8
```

**macOS/Linux (Bash)**:
```bash
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "dev-marketplace",
  "owner": {"name": "Developer"},
  "plugins": [{
    "name": "multi-agent-researcher",
    "source": "../multi-agent-researcher",
    "description": "Multi-agent research with MCP search"
  }]
}
EOF
```

---

## Step 5: Install in Claude Code

```bash
# Start Claude Code
claude

# In Claude Code, run:
/plugin marketplace add ./dev-marketplace
/plugin install multi-agent-researcher@dev-marketplace
/plugin enable multi-agent-researcher
```

**Expected Output**:
```
✅ Marketplace added: dev-marketplace
✅ Plugin installed: multi-agent-researcher v2.4.0
✅ Plugin enabled
```

---

## Step 6: Verify Installation

### Test 1: Check Plugin Status
```
/plugin list
```
Should show `multi-agent-researcher` as **enabled**.

### Test 2: Test Commands
Type `/research` - should see autocomplete with:
- /research
- /research-quick
- /research-deep

### Test 3: Run Test Research
```
/research-quick test installation
```

**Expected**:
- 🚀 Skill activation message
- 2 researchers spawned
- Progress notifications
- Report generated in 10-15 minutes

---

## Troubleshooting

### "Plugin not found"

**Check**:
1. Marketplace path correct: `ls dev-marketplace/.claude-plugin/`
2. Source path in marketplace.json: `"source": "../multi-agent-researcher"`
3. Plugin directory exists: `ls ../multi-agent-researcher/`

**Fix**:
```
/plugin marketplace remove dev-marketplace
/plugin marketplace add ./dev-marketplace
/plugin install multi-agent-researcher@dev-marketplace
```

### "MCP server failed to start"

**Check**:
1. API keys set: `echo $env:EXA_API_KEY` (Windows) or `echo $EXA_API_KEY` (Mac/Linux)
2. Internet connection active
3. `.mcp.json` syntax valid: `cat .mcp.json | jq .`

**Fix**:
- Restart Claude Code
- Reinstall plugin
- Check API key status in provider dashboards

### "Command not recognized"

**Check**:
1. Plugin enabled: `/plugin list`
2. Commands directory exists: `ls commands/`
3. Command files valid: `ls commands/*.md`

**Fix**:
- Restart Claude Code
- Disable and re-enable plugin
- Reinstall plugin

### First-time Brave/Perplexity slow

**Expected**: First use auto-installs packages (~30 seconds)

**Subsequent uses**: Instant

---

## Uninstallation

```
/plugin disable multi-agent-researcher
/plugin uninstall multi-agent-researcher@dev-marketplace
/plugin marketplace remove dev-marketplace
```

---

## Upgrading

```bash
# Pull latest changes
cd multi-agent-researcher
git pull origin main

# In Claude Code
/plugin uninstall multi-agent-researcher@dev-marketplace
/plugin install multi-agent-researcher@dev-marketplace
```

---

## Support

- Documentation: See `PLUGIN_README.md`
- Testing: See `TESTING.md`
- Issues: [repo-url]/issues
- Discussions: [repo-url]/discussions
