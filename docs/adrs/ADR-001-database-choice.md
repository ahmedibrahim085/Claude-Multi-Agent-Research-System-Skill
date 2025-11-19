# ADR-001: Database Choice (PostgreSQL)

**Status**: Accepted

**Date**: 2025-11-19

**Deciders**: Technical Lead, System Architect

**Tags**: database, infrastructure, persistence

---

## Context

TaskFlow requires a persistent data store for user accounts, tasks, lists, tags, and their relationships. The database must:

1. Support ACID transactions for data integrity
2. Handle relational data efficiently (users → tasks → lists, many-to-many tags)
3. Scale to 1M+ tasks with good performance
4. Support full-text search for task titles/descriptions
5. Provide JSON/JSONB support for future flexibility
6. Be cost-effective for solo/small team deployment
7. Have strong ORM support for TypeScript
8. Support both self-hosted and managed cloud deployments

**Key Requirements**:
- **Performance**: <100ms for indexed queries with 100K+ tasks per user
- **Budget**: Free or low-cost managed options available
- **Developer Experience**: Easy local development, migrations, and testing
- **Community**: Large ecosystem, active development, good documentation

---

## Decision

We will use **PostgreSQL 14+** as the primary database for TaskFlow.

---

## Rationale

### Why PostgreSQL?

#### 1. **ACID Compliance & Data Integrity**
- Full ACID transaction support ensures data consistency
- Critical for financial-grade data integrity (tasks can't be lost or corrupted)
- Row-level locking prevents race conditions in multi-user scenarios
- Atomic operations for complex task updates (e.g., changing status + updating timestamp)

#### 2. **Relational Model Fits Domain Perfectly**
TaskFlow's data model is inherently relational:
```
Users (1) ──→ (N) Tasks
Tasks (N) ──→ (1) Lists
Tasks (N) ──→ (N) Tags (via junction table)
```

PostgreSQL excels at:
- Foreign key constraints (enforce referential integrity)
- JOIN operations (fetch task with list and tags in one query)
- Cascade deletes (when user is deleted, tasks are automatically removed)
- Complex filtering (status + priority + list + tags)

#### 3. **Advanced Features**

**Full-Text Search**:
```sql
-- Built-in full-text search without external service
CREATE INDEX idx_tasks_search ON tasks
USING GIN(to_tsvector('english', title || ' ' || description));

SELECT * FROM tasks
WHERE to_tsvector('english', title || ' ' || description)
  @@ to_tsquery('architecture & design');
```

**JSON/JSONB Support**:
- Store flexible metadata without schema changes
- Future-proof for custom fields (post-MVP feature)
- Query JSON fields with SQL: `SELECT * FROM tasks WHERE metadata->>'priority' = 'high'`

**Array Types**:
- Store tags as arrays if needed: `tags TEXT[]`
- Efficient array operations: `tags @> ARRAY['work']`

#### 4. **Performance & Scalability**
- **Indexing**: B-tree, GIN, GIST indexes for different query patterns
- **Query Planner**: Sophisticated optimizer for complex queries
- **Partitioning**: Table partitioning by user_id for massive scale (future)
- **Read Replicas**: Easy horizontal read scaling (supported by all cloud providers)
- **Connection Pooling**: PgBouncer for efficient connection reuse

**Benchmark** (100K tasks, indexed by user_id):
```sql
-- Typical task list query
SELECT * FROM tasks WHERE user_id = 'uuid' AND status = 'in_progress' LIMIT 25;
-- Result: ~15ms (with index)

-- Complex filter query
SELECT * FROM tasks
WHERE user_id = 'uuid'
  AND status IN ('not_started', 'in_progress')
  AND priority IN ('high', 'urgent')
  AND due_date <= '2025-12-31'
ORDER BY due_date ASC
LIMIT 25;
-- Result: ~25ms (with composite index)
```

#### 5. **Developer Experience**
- **Prisma ORM**: Excellent TypeScript support, type-safe queries, auto-generated client
  ```typescript
  const tasks = await prisma.task.findMany({
    where: { userId, status: 'in_progress' },
    include: { list: true, tags: true }
  });
  // tasks is fully typed, no casting needed
  ```
- **Migrations**: Prisma Migrate for version-controlled schema changes
- **Local Development**: Docker container, instant setup
- **GUI Tools**: pgAdmin, DBeaver, Prisma Studio (built-in)

#### 6. **Cost-Effectiveness**

**Free Tier Options**:
- Railway.app: Free 500MB PostgreSQL (perfect for MVP)
- Supabase: Free 500MB + 2GB bandwidth
- Neon: Free 3GB serverless PostgreSQL

**Paid Options** (for growth):
- DigitalOcean Managed PostgreSQL: $15/month (1GB RAM, 10GB storage, automated backups)
- AWS RDS (t4g.micro): $16/month (1GB RAM, 20GB storage)
- Supabase Pro: $25/month (8GB, point-in-time recovery)

**Self-Hosted**: Free (just compute costs)

#### 7. **Ecosystem & Community**
- 30+ years of development (first release: 1996)
- Active development (major release yearly)
- Massive community (Stack Overflow: 400K+ questions)
- Enterprise-grade support available (if needed)
- Used by: Instagram, Spotify, Reddit, Uber, Netflix

#### 8. **Open Source & No Vendor Lock-In**
- MIT-style PostgreSQL License (truly open source)
- Standard SQL compliance (easy migration to/from other SQL databases)
- No proprietary features required for our use case
- Can switch cloud providers without database changes

---

## Alternatives Considered

### MySQL
**Pros**:
- Slightly faster for simple read queries
- Wider adoption in shared hosting environments
- Familiar to many developers

**Cons**:
- Weaker JSON support (until MySQL 8.0)
- Less sophisticated query optimizer
- Transaction isolation issues (repeatable read default can cause phantom reads)
- No full-text search for InnoDB (FULLTEXT index only for MyISAM in older versions)
- Foreign key constraints sometimes buggy (historical issues)

**Verdict**: ❌ **Rejected** - PostgreSQL's advanced features outweigh MySQL's marginal performance gains

---

### MongoDB
**Pros**:
- Flexible schema (no migrations)
- Horizontal sharding built-in
- Good for document-based data

**Cons**:
- **No ACID transactions in MVP use case** (transactions limited to single document in older versions)
- **Poor fit for relational data**:
  - No native JOINs (requires $lookup aggregation, slow)
  - Many-to-many relationships cumbersome (embed or reference trade-offs)
  - Data duplication (denormalization) required for performance
- **Larger storage footprint** (BSON overhead)
- **Query performance unpredictable** without proper indexing strategy
- **Weaker data integrity** (no foreign key constraints, application-level enforcement)

**Example Problem**:
```javascript
// MongoDB: To get task with list and tags, need 3 queries or complex aggregation
const task = await db.tasks.findOne({ _id: taskId });
const list = await db.lists.findOne({ _id: task.list_id });
const tags = await db.tags.find({ _id: { $in: task.tag_ids } });

// PostgreSQL: Single query with JOINs
const task = await prisma.task.findUnique({
  where: { id: taskId },
  include: { list: true, tags: true }
});
```

**Verdict**: ❌ **Rejected** - Relational data model is a poor fit for document database

---

### SQLite
**Pros**:
- Zero configuration (file-based)
- Perfect for local development
- Very fast for single-user scenarios
- Embedded (no server process)

**Cons**:
- **No concurrent writes** (database lock on write)
- **Limited scalability** (single file on single server)
- **No network access** (can't separate app and DB servers)
- **Weaker data types** (no native date/time types, everything is text/int/blob)
- **No ALTER TABLE support** for many operations (requires recreate table)
- **No built-in replication or backups** (manual file copies)

**Use Case**: ❌ **Rejected for production**, ✅ **Accepted for testing/development** (in-memory mode for fast unit tests)

---

### Firebase/Firestore (NoSQL)
**Pros**:
- Real-time sync out of the box
- Generous free tier
- Simple API

**Cons**:
- **Vendor lock-in** (proprietary Google service)
- **Query limitations** (no complex joins, limited filtering)
- **Cost unpredictability** (charges per read/write, can spike)
- **No ACID transactions across documents**
- **Migration complexity** (hard to export and move to self-hosted)

**Verdict**: ❌ **Rejected** - Vendor lock-in and cost concerns

---

### Supabase (PostgreSQL + Services)
**Pros**:
- PostgreSQL under the hood
- Built-in auth, real-time, storage
- Generous free tier
- Great developer experience

**Cons**:
- **Not a separate option** (uses PostgreSQL, which we already chose)
- **Vendor lock-in for extra features** (auth, real-time, storage are proprietary)
- **Can't easily self-host** (Supabase is complex to deploy)

**Verdict**: ✅ **Accepted as hosting option**, not as database alternative

---

## Consequences

### Positive Consequences

1. **Type Safety Across Stack**
   - Prisma generates TypeScript types from schema
   - Compile-time errors for mismatched queries
   - Auto-complete in IDE

2. **Simplified Data Model**
   - Foreign keys enforce relationships
   - Cascade deletes reduce manual cleanup
   - Constraints prevent invalid data

3. **Future-Proof**
   - Partition tables by user_id if scaling beyond 10M tasks
   - Add read replicas for reporting without code changes
   - Upgrade to TimescaleDB for time-series task analytics (future)

4. **Testing Simplified**
   - Prisma supports SQLite for fast in-memory tests
   - Same API for development (SQLite) and production (PostgreSQL)

5. **Operational Simplicity**
   - Managed options (DigitalOcean, AWS RDS, Supabase) handle backups, updates, monitoring
   - Point-in-time recovery for disaster scenarios
   - Automated failover in multi-node setups

### Negative Consequences

1. **Learning Curve**
   - Developers unfamiliar with SQL/PostgreSQL need training
   - Understanding indexing strategy requires database knowledge
   - Query optimization needs EXPLAIN ANALYZE skills

   **Mitigation**:
   - Prisma ORM abstracts most SQL complexity
   - Document common query patterns in `/docs/database-patterns.md`
   - Use Prisma Studio for visual query building

2. **Schema Migrations**
   - Schema changes require migrations (not schema-less like MongoDB)
   - Downtime possible for large schema changes (rare)

   **Mitigation**:
   - Prisma Migrate automates migration creation
   - Blue-green deployment for zero-downtime migrations
   - Test migrations in staging first

3. **Vertical Scaling Limits**
   - Single PostgreSQL instance limited by server resources
   - Write scaling harder than NoSQL (can't just add nodes)

   **Mitigation**:
   - Add read replicas for read-heavy workloads (95% of queries are reads)
   - Partition large tables (user_id sharding) when reaching limits
   - Use caching (Redis) to reduce database load

4. **Cost at Massive Scale**
   - High-spec PostgreSQL instances expensive ($500+/month for 32GB RAM)
   - Replication increases costs linearly

   **Mitigation**:
   - At current target scale (10K users), cost is minimal ($15-60/month)
   - By the time scaling is an issue, revenue should support infrastructure
   - Optimize queries and caching before scaling hardware

---

## Implementation Notes

### Initial Schema (Prisma)
```prisma
model User {
  id           String   @id @default(uuid())
  email        String   @unique
  passwordHash String
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  tasks        Task[]
  lists        List[]
}

model Task {
  id          String    @id @default(uuid())
  title       String    @db.VarChar(255)
  description String?   @db.Text
  status      Status    @default(NOT_STARTED)
  priority    Priority  @default(MEDIUM)
  dueDate     DateTime? @db.Date
  completedAt DateTime?
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
  userId      String
  user        User      @relation(fields: [userId], references: [id])
  listId      String?
  list        List?     @relation(fields: [listId], references: [id])
  tags        TaskTag[]

  @@index([userId, status])
  @@index([userId, dueDate])
}
```

### Required PostgreSQL Extensions
```sql
-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Trigram similarity

-- Query performance analysis
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

### Recommended Connection Pool Settings
```env
# DATABASE_URL format
DATABASE_URL="postgresql://user:password@localhost:5432/taskflow?schema=public&connection_limit=20&pool_timeout=10"

# Prisma connection pool
# Max connections = (CPU cores * 2) + effective_spindle_count
# For 2 CPU server: 10-20 connections
```

### Backup Script
```bash
#!/bin/bash
# Daily backup cron job
pg_dump $DATABASE_URL | gzip > /backups/taskflow_$(date +%Y%m%d).sql.gz
find /backups -name "taskflow_*.sql.gz" -mtime +30 -delete
```

---

## Related Decisions

- **ADR-002**: Frontend Framework (React + TypeScript) - Shares TypeScript types with Prisma
- **ADR-005**: State Management (Zustand) - Client-side state complements server state in PostgreSQL

---

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Prisma Documentation](https://www.prisma.io/docs)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Database Schema Design Best Practices](https://www.postgresql.org/docs/current/ddl.html)

---

**Reviewed By**: Technical Lead, Database Specialist
**Approved**: 2025-11-19
**Next Review**: After MVP deployment (Month 3)
