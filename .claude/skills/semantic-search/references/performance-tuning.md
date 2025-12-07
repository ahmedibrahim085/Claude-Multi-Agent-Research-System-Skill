# Performance Tuning Guide for Semantic Code Search

**Optimize search performance, manage index size, and handle large codebases efficiently.**

This guide helps you get the best performance from semantic code search, especially when working with large codebases (>10k files) or complex queries.

## Table of Contents

1. [Understanding Performance](#understanding-performance)
2. [Optimal k Value Selection](#optimal-k-value-selection)
3. [Large Codebase Strategies](#large-codebase-strategies)
4. [Query Optimization](#query-optimization)
5. [Index Management](#index-management)
6. [System Resource Tuning](#system-resource-tuning)

---

## Understanding Performance

### Performance Factors

Semantic search performance is affected by:

1. **Index Size**: Larger codebases = larger indexes = slower searches
2. **k Value**: More results requested = more processing time
3. **Query Complexity**: Longer queries require more semantic processing
4. **Hardware**: CPU, RAM, and disk I/O all matter

### Typical Performance Benchmarks

| Codebase Size | Index Size | Search Time (k=5) | Search Time (k=50) |
|---------------|------------|-------------------|-------------------|
| Small (100 files) | ~5 MB | <100ms | <200ms |
| Medium (1,000 files) | ~50 MB | <500ms | <1s |
| Large (10,000 files) | ~500 MB | 1-3s | 3-10s |
| Very Large (100,000 files) | ~5 GB | 5-15s | 15-60s |

**Note**: These are approximate. Actual performance depends on file types, code density, and hardware.

---

## Optimal k Value Selection

### Corner Case #5: k Value Guidelines

The `--k` parameter controls how many results are returned. Choosing the right value is critical for performance.

### Recommended k Ranges

| Use Case | Recommended k | Rationale |
|----------|---------------|-----------|
| Quick exploration | **k=5** (default) | Fast, usually enough to find what you need |
| Thorough search | **k=10-20** | Good balance of coverage and speed |
| Exhaustive analysis | **k=30-50** | Comprehensive but slower |
| Avoid | **k>100** | Extremely slow, massive output, rarely useful |

### Performance Impact

```bash
# Fast (< 1s on medium codebase)
python scripts/search.py --query "authentication" --k 5

# Moderate (1-3s on medium codebase)
python scripts/search.py --query "authentication" --k 20

# Slow (3-10s on medium codebase)
python scripts/search.py --query "authentication" --k 50

# Very Slow (10-60s on medium codebase)
python scripts/search.py --query "authentication" --k 100

# Extremely Slow (may timeout or exhaust memory)
python scripts/search.py --query "authentication" --k 1000
```

### Memory Implications

**k value impacts memory usage**:

- **k=5**: ~1 MB of result data
- **k=50**: ~10 MB of result data
- **k=500**: ~100 MB of result data
- **k=5000**: ~1 GB of result data (may fail!)

**Rule of Thumb**: Keep k < 100 unless you have a specific reason and ample RAM.

### When to Use High k Values

**Legitimate use cases for k>50**:

1. **Statistical Analysis**: Analyzing distribution of implementations across codebase
2. **Bulk Operations**: Feeding results to automated processing scripts
3. **Comprehensive Audits**: Security audits requiring exhaustive coverage

**For these cases, consider**:
```bash
# Stream output to file instead of terminal
python scripts/search.py --query "auth" --k 500 > results.json

# Process incrementally
python scripts/search.py --query "auth" --k 500 | jq -c '.data.results[]' | while read result; do
  # Process each result individually
  echo $result | jq '.file_path'
done
```

---

## Large Codebase Strategies

### Strategy 1: Narrow Your Scope

Instead of searching entire monorepo, search subdirectories:

```bash
# Slow: Search entire monorepo index
cd ~/monorepo
python ~/.claude/skills/searching-code-semantically/scripts/search.py --query "auth"

# Faster: Index and search specific service
cd ~/monorepo/services/auth-service
# Index this directory (using MCP server)
# Then search
python ~/.claude/skills/searching-code-semantically/scripts/search.py --query "token validation"
```

**Benefit**: Smaller index = faster searches, more relevant results.

### Strategy 2: Multiple Targeted Indexes

Maintain separate indexes for different parts of your codebase:

```bash
# Index structure:
~/project/frontend/.code-search-index/
~/project/backend/.code-search-index/
~/project/shared/.code-search-index/

# Search specific subsystem
cd ~/project/backend
python scripts/search.py --query "database queries" --storage-dir .code-search-index
```

**Benefit**: Each index is smaller and faster. You search only where you expect results.

**Tradeoff**: Can't discover cross-subsystem patterns in a single query.

### Strategy 3: File Type Filtering via Index Configuration

When creating the index (via MCP server), exclude file types you'll never search:

**Exclude**:
- Binary files (.png, .jpg, .pdf)
- Generated code (dist/, build/, node_modules/)
- Vendored dependencies (vendor/, third_party/)
- Documentation (docs/) if you only search code

**Benefit**: Smaller index, faster searches, fewer false positives.

**Configuration** (when indexing via MCP server):
```python
# Example (if MCP server supports it):
index_directory(
    path="/path/to/code",
    file_patterns=["*.js", "*.ts", "*.py", "*.go"],  # Only code files
    exclude_patterns=["*/node_modules/*", "*/dist/*", "*/.git/*"]
)
```

### Strategy 4: Smart Auto-Reindex (IndexFlatIP)

The current implementation uses **IndexFlatIP** (same as MCP's `claude-context-local`) with smart auto-reindex:

**How it works**:
- **Merkle tree** detects when files have changed (fast detection)
- **Auto-fallback** performs full reindex when changes detected (clears + rebuilds all)
- **No incremental updates**: IndexFlatIP uses sequential IDs (0, 1, 2...), doesn't support selective vector updates

**Performance**:
```bash
# Full reindex: 3-10 minutes for medium codebase (~6,000 chunks)
# Change detection: <1 second (Merkle tree)
# No changes: Skips reindex entirely (instant)
```

**Why full reindex**:
- IndexFlatIP cannot remove individual vectors (sequential IDs)
- Ensures no stale data or synchronization issues
- Same proven approach used by MCP (reliable, cross-platform)

**Optimization**: Auto-reindex only rebuilds when files actually changed, saving time compared to unconditional full reindex.

### Strategy 5: SSD vs HDD

**Index location matters**:

- ✅ **Store index on SSD**: 5-10x faster searches
- ❌ **Store index on HDD**: Painfully slow, especially for large indexes
- ⚠️ **Store index on network drive**: Very slow, not recommended

**Move index to SSD**:
```bash
# Move index to SSD
mv .code-search-index ~/ssd-drive/.code-search-index

# Search with custom path
python scripts/search.py --query "auth" --storage-dir ~/ssd-drive/.code-search-index
```

---

## Query Optimization

### Fast Queries vs Slow Queries

**Fast Queries** (low semantic complexity):
```bash
✅ "user authentication"  # Simple, clear concept
✅ "database connection pooling"  # Well-defined pattern
✅ "HTTP POST request"  # Specific action
```

**Slow Queries** (high semantic complexity):
```bash
⚠️ "complex business logic that handles user authentication, authorization, session management, and also logging with error handling and retry mechanisms"
# Too many concepts, forces semantic model to compare against many vectors
```

**Optimization**: Break complex queries into multiple simpler queries:

```bash
# Instead of one mega-query:
python scripts/search.py --query "authentication with sessions and logging and retries" --k 10

# Do multiple focused queries:
python scripts/search.py --query "user authentication with sessions" --k 5
python scripts/search.py --query "authentication logging" --k 5
python scripts/search.py --query "retry logic" --k 5
```

**Benefit**: Faster individual searches, more precise results.

### Query Length Sweet Spot

**Optimal query length**: 3-8 words

```bash
# Too short (may be ambiguous)
❌ "auth"  # Could match many things

# Good length (clear, specific)
✅ "user authentication with JWT"  # 4 words, clear intent

# Too long (slow, overly specific)
❌ "user authentication using JSON Web Tokens with RS256 signature algorithm and 1-hour expiration time"  # 15 words, too much
```

---

## Index Management

### Index Size Monitoring

**Check index size regularly**:

```bash
# macOS/Linux
du -sh .code-search-index/

# Expected sizes:
# Small project: 5-50 MB
# Medium project: 50-500 MB
# Large project: 500 MB - 5 GB
# Huge project: >5 GB (consider splitting)
```

**If index >2 GB**, consider:
1. Splitting into multiple indexes (frontend/backend)
2. Excluding vendored code
3. Excluding generated files

### Index Freshness

**Stale index symptoms**:
- Search returns old code that's been refactored
- New files don't appear in results
- Deleted files still appear

**Solution**: Reindex periodically.

```bash
# Strategy 1: Manual reindexing
# Delete old index
rm -rf .code-search-index

# Rebuild (via MCP server)
# <indexing command>

# Strategy 2: Scheduled reindexing
# Add to cron/scheduled tasks
# 0 2 * * * cd ~/project && <reindex command>  # Every night at 2am
```

**Recommendation**:
- **Active development**: Reindex daily or weekly
- **Stable codebase**: Reindex monthly
- **Read-only archive**: Reindex once

### Index Compression

**SQLite compression**:

```bash
# Vacuum the database to reclaim space
sqlite3 .code-search-index/vector_store.db "VACUUM;"

# Before: 500 MB
# After: 350 MB (typical 20-30% reduction)
```

**When to vacuum**:
- After deleting many files from codebase
- After initial indexing (cleans up temp space)
- Monthly for active projects

---

## System Resource Tuning

### Memory Recommendations

**Minimum RAM**:
- Small codebase (<1k files): 2 GB RAM
- Medium codebase (1-10k files): 4 GB RAM
- Large codebase (10-100k files): 8 GB RAM
- Very large codebase (>100k files): 16+ GB RAM

**If searches are slow due to memory**:

```bash
# Check memory usage during search
python scripts/search.py --query "test" --k 50 &
PID=$!
ps aux | grep $PID
# Look at RSS (resident set size)
```

**Symptoms of memory pressure**:
- Searches take progressively longer
- System swapping to disk
- Other applications slow down

**Solutions**:
1. Close other applications
2. Reduce k value
3. Split index into smaller chunks
4. Upgrade RAM

### CPU Utilization

Semantic search is CPU-intensive (vector similarity calculations).

**Monitor CPU**:
```bash
# macOS
top -pid $(pgrep -f search.py)

# Linux
htop -p $(pgrep -f search.py)
```

**Multi-core utilization**: Check if the MCP server's searcher uses multiple cores. If yes, searches scale with CPU cores. If no, limited to single-core performance.

**Optimization**:
- Close background CPU-intensive tasks
- Run searches on a machine with faster single-core performance
- If searching frequently, consider dedicated search instance

### Disk I/O Optimization

**Index is I/O-intensive**:

```bash
# Monitor disk I/O during search
iostat -x 1  # Linux
sudo fs_usage -w | grep search.py  # macOS
```

**Optimization**:
1. **Use SSD** (as mentioned earlier)
2. **Increase filesystem cache**: More RAM allocated to disk cache helps
3. **Reduce index size**: Fewer files = less I/O

---

## Performance Troubleshooting

### Symptom: Searches taking >30s

**Checklist**:
1. Check k value: Is it >100? Reduce it.
2. Check index size: Is it >5 GB? Split it.
3. Check disk: Is index on HDD? Move to SSD.
4. Check RAM: Is system swapping? Close other apps or reduce k.
5. Check query: Is it >10 words? Simplify it.

### Symptom: Out of memory errors

**Error**:
```bash
MemoryError: Unable to allocate X MB
```

**Solutions**:
1. **Immediate**: Reduce k value to 5-10
2. **Short-term**: Close other applications, free RAM
3. **Long-term**: Split index, upgrade RAM

### Symptom: "Database is locked" errors

**Cause**: Concurrent access (see [troubleshooting.md](troubleshooting.md) CC#4)

**Solution**: Wait for ongoing operations to complete, don't run searches while indexing.

---

## Best Practices Summary

### ✅ DO

1. **Start with k=5**, increase only if needed
2. **Use SSD** for index storage
3. **Index only what you search** (exclude vendored code, generated files)
4. **Reindex periodically** to keep results fresh
5. **Monitor index size** and split if >2 GB
6. **Keep queries focused** (3-8 words)
7. **Vacuum database** monthly for active projects

### ❌ DON'T

1. **Don't use k>100** unless absolutely necessary
2. **Don't store index on HDD** or network drives
3. **Don't index everything** (binary files, node_modules, etc.)
4. **Don't let index go stale** for months
5. **Don't run concurrent indexing + searching**
6. **Don't use 15+ word queries**

---

## Advanced: Benchmarking Your Setup

**Create a performance baseline**:

```bash
# 1. Small query, small k
time python scripts/search.py --query "authentication" --k 5

# 2. Medium query, medium k
time python scripts/search.py --query "user session management with Redis" --k 20

# 3. Large query, large k
time python scripts/search.py --query "database connection pooling" --k 50
```

**Record results**:
```
Baseline (date):
- Small: 0.8s
- Medium: 2.3s
- Large: 8.1s
```

**Compare after optimizations**:
```
After moving to SSD:
- Small: 0.3s (2.7x faster)
- Medium: 1.1s (2.1x faster)
- Large: 3.2s (2.5x faster)
```

---

## Performance Checklist

Before reporting performance issues, verify:

- [ ] Index is on SSD (not HDD)
- [ ] k value is reasonable (<50)
- [ ] Query is focused (3-8 words)
- [ ] Index size is reasonable (<2 GB)
- [ ] Index has been vacuumed recently
- [ ] Sufficient RAM available (8+ GB for large codebases)
- [ ] No concurrent indexing operations
- [ ] No system resource exhaustion (swap, CPU saturation)

**If all checks pass and performance is still poor**, the issue may be with the underlying MCP server. Consult `claude-context-local` performance documentation.

---

**Next Steps**: If you're experiencing performance issues, review this checklist and apply optimizations. For functional issues, see [troubleshooting.md](troubleshooting.md).
