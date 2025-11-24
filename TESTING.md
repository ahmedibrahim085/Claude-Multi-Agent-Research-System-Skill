# Plugin Testing Guide

## Prerequisites
- Claude Code installed
- Plugin installed and enabled
- API keys configured (EXA, TAVILY, BRAVE, PERPLEXITY)

---

## Quick Test (5 minutes)

### Test 1: Command Availability
Type `/research` in Claude Code - commands should appear in autocomplete:
- `/research`
- `/research-quick`
- `/research-deep`

✅ **Pass**: All 3 commands visible  
❌ **Fail**: Commands not found → Restart Claude Code

### Test 2: Basic Research
```
/research-quick artificial intelligence
```

**Expected Results**:
- ✅ 2 researchers spawned
- ✅ Progress notifications appear
- ✅ Report generated in `files/reports/`
- ✅ Time: ~10 minutes

### Test 3: MCP Tools
After research completes, check research notes in `files/research_notes/`:
- ✅ Should reference `exa_search`, `tavily_search`, `brave_search`, or `perplexity_search`
- ✅ Sources from multiple search engines

---

## Full Test Suite (30 minutes)

### Test 4: Standard Research
```
/research quantum computing
```

**Verify**:
- ✅ 3 subtopics decomposed (check TodoWrite or initial message)
- ✅ Parallel researcher execution
- ✅ MCP tools utilized (check notes)
- ✅ Report synthesis by report-writer agent
- ✅ Files in correct locations:
  - `files/research_notes/*.md` (3 files)
  - `files/reports/quantum-computing_*.md` (1 file)

### Test 5: Deep Research
```
/research-deep blockchain regulation
```

**Verify**:
- ✅ 4 subtopics
- ✅ Longer completion time (~25-30 min)
- ✅ More comprehensive report
- ✅ 4 research note files

### Test 6: Hooks (if supported)
Check logs for hook execution:
- ✅ 🚀 Skill activation message
- ✅ 🔬 Researcher spawn logs
- ✅ 📝 Synthesis start log
- ✅ 📊 Report generation log

### Test 7: Memory (if supported)
After research completion:
- ✅ Session memory persisted
- ✅ All fields populated (topic, date, subtopics, report_path, sources_count)

### Test 8: Error Handling
Intentionally cause errors:
- Turn off internet → Should fall back gracefully
- Invalid API key → Should document failure and continue

---

## Troubleshooting

### Issue: MCP Tools Not Available

**Symptoms**: Researchers only use WebSearch

**Solutions**:
1. Check `.mcp.json` syntax: `cat .mcp.json | jq .`
2. Verify API keys in environment:
   ```powershell
   echo $env:EXA_API_KEY
   echo $env:TAVILY_API_KEY
   ```
3. Restart Claude Code
4. Check MCP server status in Claude Code settings

### Issue: Hooks Not Firing

**Symptoms**: No emoji logs, directories not auto-created

**Solutions**:
1. Check `hooks/hooks.json` syntax: `cat hooks/hooks.json | jq .`
2. Verify hook conditions match tool names
3. Restart Claude Code
4. Check if hooks are supported in your Claude Code version

### Issue: Slow Performance

**Expected Behavior**:
- Brave/Perplexity first-time install: ~30s
- Each researcher: ~5-10 min
- Total research: 15-30 min

**If slower**:
- Check internet connection
- Verify API rate limits not exceeded
- Check system resources

### Issue: Plugin Not Found

**Solutions**:
1. Verify marketplace added: `/plugin marketplace list`
2. Check marketplace.json syntax
3. Verify source path in marketplace.json
4. Reinstall: `/plugin install multi-agent-researcher@dev-marketplace`

### Issue: Commands Not Recognized

**Solutions**:
1. Verify plugin enabled: `/plugin list`
2. Check `commands/` directory exists with .md files
3. Restart Claude Code
4. Reinstall plugin

---

## Performance Benchmarks

| Depth | Subtopics | Researchers | Avg Time | Report Length |
|-------|-----------|-------------|----------|---------------|
| Quick | 2 | 2 | ~10 min | 5-10 pages |
| Standard | 3 | 3 | ~15-20 min | 10-20 pages |
| Deep | 4 | 4 | ~25-30 min | 20-30 pages |

---

## Test Checklist

- [ ] Commands autocomplete
- [ ] Quick research completes
- [ ] MCP tools used
- [ ] Standard research (3 subtopics)
- [ ] Deep research (4 subtopics)
- [ ] Hook logs appear
- [ ] Memory persists
- [ ] Error handling works
- [ ] Files in correct locations
- [ ] Report quality acceptable

**Status**: ___/10 tests passed

---

## Reporting Issues

If tests fail, collect:
1. Claude Code version
2. Plugin version (check plugin.json)
3. Error messages
4. Log files
5. Steps to reproduce

Create issue at: [repo-url]/issues
