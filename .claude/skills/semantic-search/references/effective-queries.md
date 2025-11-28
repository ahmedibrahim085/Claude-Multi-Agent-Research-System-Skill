# Effective Query Patterns for Semantic Code Search

**Master the art of semantic search queries to find code by functionality, not keywords.**

This guide teaches you how to craft effective natural language queries for semantic code search. Unlike traditional Grep/regex searches that match exact text, semantic search understands **meaning**, so query formulation requires different skills.

## Table of Contents

1. [General Query Principles](#general-query-principles)
2. [Query Patterns by Category](#query-patterns-by-category)
3. [Good vs Bad Examples](#good-vs-bad-examples)
4. [Domain-Specific Patterns](#domain-specific-patterns)
5. [Advanced Techniques](#advanced-techniques)
6. [Query Debugging](#query-debugging)

---

## General Query Principles

### ✅ DO: Focus on Functionality

**Good**: Describe what the code **does**
- "user authentication with JWT tokens"
- "database connection pooling"
- "retry logic for HTTP requests"

**Bad**: Use exact variable names you're guessing
- "authenticateUser function" (might be named `verifyUser`, `loginHandler`, etc.)
- "dbPool variable" (might be `connectionPool`, `pool`, `dbConnections`)

### ✅ DO: Use Common Terminology

**Good**: Use widely-understood technical terms
- "OAuth 2.0 authorization flow"
- "exponential backoff retry strategy"
- "pagination with cursor-based navigation"

**Bad**: Use project-specific jargon without context
- "the flannel pattern" (internal nickname)
- "widget thing we discussed" (vague)

### ✅ DO: Be Specific About Context

**Good**: Include relevant context
- "file upload validation for images"
- "credit card payment processing with Stripe"
- "user session management with Redis"

**Bad**: Be overly generic
- "validation" (too broad - validating what?)
- "payment" (credit card? invoice? subscription?)
- "cache" (what's being cached? how?)

### ❌ DON'T: Use Exact Code Syntax

**Bad**: Literal code snippets
- `if (user.isAuthenticated)`
- `async function getUserById`
- `SELECT * FROM users WHERE`

**Good**: Describe the logic conceptually
- "check if user is authenticated"
- "asynchronous user lookup by ID"
- "SQL query to retrieve all users"

### ❌ DON'T: Assume Naming Conventions

**Bad**: Guess function/variable names
- "handleSubmit function"
- "API_KEY constant"
- "validateEmail method"

**Good**: Describe the behavior
- "form submission handling"
- "API key configuration"
- "email address validation"

---

## Query Patterns by Category

### 🔐 Authentication & Authorization

**Effective Patterns**:
```
✅ "user login with password hashing"
✅ "JWT token generation and validation"
✅ "OAuth 2.0 authorization code flow"
✅ "role-based access control checking"
✅ "session cookie management"
✅ "API key authentication middleware"
✅ "two-factor authentication implementation"
✅ "password reset flow with email verification"
```

**Why These Work**: Combine the action (login, validate, check) with the mechanism (JWT, OAuth, RBAC) and optionally the security detail (hashing, 2FA).

### 🗄️ Database & Persistence

**Effective Patterns**:
```
✅ "database transaction with rollback handling"
✅ "SQL query with JOIN across multiple tables"
✅ "MongoDB aggregation pipeline for analytics"
✅ "database migration script for schema changes"
✅ "ORM model definition with relationships"
✅ "connection pooling configuration"
✅ "database query pagination"
✅ "soft delete implementation"
```

**Why These Work**: Specify the database operation, the technology (SQL, MongoDB, ORM), and the specific pattern (transaction, JOIN, aggregation).

### 🌐 HTTP & API

**Effective Patterns**:
```
✅ "HTTP GET request with query parameters"
✅ "REST API endpoint with JSON response"
✅ "GraphQL query resolver"
✅ "HTTP request retry logic with exponential backoff"
✅ "API rate limiting implementation"
✅ "CORS configuration for cross-origin requests"
✅ "request timeout handling"
✅ "multipart form data upload"
```

**Why These Work**: Include HTTP method/protocol (GET, REST, GraphQL), the action (retry, rate limit), and the data format (JSON, multipart).

### 🔄 Async & Concurrency

**Effective Patterns**:
```
✅ "asynchronous file reading with promises"
✅ "parallel execution with Promise.all"
✅ "worker thread pool for CPU-intensive tasks"
✅ "event emitter for pub-sub pattern"
✅ "race condition prevention with locks"
✅ "async/await error handling"
✅ "debouncing rapid function calls"
✅ "throttling API requests"
```

**Why These Work**: Specify async primitive (promises, workers, events), the concurrency pattern (parallel, pub-sub, locks), and the purpose.

### ⚠️ Error Handling

**Effective Patterns**:
```
✅ "try-catch error handling with logging"
✅ "custom error class definitions"
✅ "global error handler middleware"
✅ "error message internationalization"
✅ "validation error aggregation"
✅ "circuit breaker pattern for fault tolerance"
✅ "graceful shutdown on SIGTERM"
✅ "uncaught exception handler"
```

**Why These Work**: Combine error mechanism (try-catch, custom errors, circuit breaker) with the response action (logging, i18n, graceful shutdown).

### 🧪 Testing

**Effective Patterns**:
```
✅ "unit test with mocked dependencies"
✅ "integration test for API endpoints"
✅ "test fixture setup and teardown"
✅ "assertion helpers for common validations"
✅ "snapshot testing for UI components"
✅ "end-to-end test with browser automation"
✅ "test coverage reporting configuration"
✅ "parameterized tests with test cases"
```

**Why These Work**: Specify test type (unit, integration, e2e), testing technique (mocking, fixtures, snapshots), and what's being tested.

### 📁 File & Stream Operations

**Effective Patterns**:
```
✅ "read file line by line for large files"
✅ "stream processing for CSV parsing"
✅ "file upload with progress tracking"
✅ "temporary file creation and cleanup"
✅ "recursive directory traversal"
✅ "file compression with gzip"
✅ "image resizing and optimization"
✅ "file watcher for hot reload"
```

**Why These Work**: Describe the I/O operation (read, stream, upload), the file type (CSV, image), and the technique (line-by-line, compression, watcher).

---

## Good vs Bad Examples

### Example 1: Finding Authentication Logic

❌ **Bad Query**: `"auth"`
- **Problem**: Too vague. Matches authentication, authorization, author names, OAuth mentions, etc.
- **Results**: 500+ irrelevant matches

✅ **Good Query**: `"user authentication with password verification"`
- **Why Better**: Specifies the actor (user), action (authentication), and mechanism (password verification)
- **Results**: 8 highly relevant implementations

---

### Example 2: Locating Database Queries

❌ **Bad Query**: `"query"`
- **Problem**: Matches URL query strings, search queries, database queries, "query" in comments
- **Results**: 1000+ mixed matches

✅ **Good Query**: `"SQL SELECT query with WHERE clause filtering"`
- **Why Better**: Specifies technology (SQL), operation (SELECT), and pattern (WHERE filtering)
- **Results**: 15 targeted results

---

### Example 3: Finding Error Handling

❌ **Bad Query**: `"error"`
- **Problem**: Matches error variables, error messages, console.error(), throw statements, comments about errors
- **Results**: 800+ noisy matches

✅ **Good Query**: `"try-catch block with custom error logging"`
- **Why Better**: Specifies mechanism (try-catch), customization (custom), and action (logging)
- **Results**: 12 relevant examples

---

### Example 4: Discovering Caching Logic

❌ **Bad Query**: `"cache"`
- **Problem**: Matches cache variables, comments about caching, HTTP cache headers, various cache implementations
- **Results**: 300+ mixed relevance

✅ **Good Query**: `"Redis cache with TTL expiration for session data"`
- **Why Better**: Specifies technology (Redis), configuration (TTL), and purpose (session data)
- **Results**: 5 precise matches

---

### Example 5: Locating Validation

❌ **Bad Query**: `"validate"`
- **Problem**: Matches all validation everywhere - forms, data, schemas, inputs, etc.
- **Results**: 600+ broad matches

✅ **Good Query**: `"email address format validation with regex"`
- **Why Better**: Specifies what's validated (email address), aspect (format), and method (regex)
- **Results**: 10 focused results

---

## Domain-Specific Patterns

### Frontend (React/Vue/Angular)

**Effective Queries**:
```
✅ "React component with useState hook for form input"
✅ "Vue computed property for derived state"
✅ "Angular service with HTTP client injection"
✅ "React context provider for global state"
✅ "component lifecycle hook for data fetching"
✅ "event handler for button click with validation"
✅ "conditional rendering based on user permissions"
✅ "CSS-in-JS styling with theme variables"
```

**Key Elements**: Framework name + primitive (hook, computed, service) + purpose

---

### Backend (Node/Python/Java)

**Effective Queries**:
```
✅ "Express middleware for request logging"
✅ "Django view with form validation and database save"
✅ "Spring Boot controller with dependency injection"
✅ "FastAPI endpoint with Pydantic model validation"
✅ "Node.js stream pipeline for data transformation"
✅ "background job scheduling with cron"
✅ "WebSocket connection handling with Socket.io"
✅ "GraphQL schema definition with resolvers"
```

**Key Elements**: Framework + component type + specific action

---

### DevOps & Infrastructure

**Effective Queries**:
```
✅ "Docker multi-stage build for production optimization"
✅ "Kubernetes deployment with resource limits"
✅ "Terraform configuration for AWS S3 bucket"
✅ "CI/CD pipeline with automated testing"
✅ "environment variable configuration for different stages"
✅ "health check endpoint for load balancer"
✅ "logging aggregation with structured JSON logs"
✅ "metrics collection with Prometheus"
```

**Key Elements**: Tool name + configuration aspect + optimization/purpose

---

### Data Processing & ML

**Effective Queries**:
```
✅ "Pandas DataFrame filtering with multiple conditions"
✅ "NumPy array transformation and reshaping"
✅ "PyTorch model training loop with validation"
✅ "data normalization and feature scaling"
✅ "batch processing for large dataset iteration"
✅ "cross-validation for model evaluation"
✅ "hyperparameter tuning with grid search"
✅ "model serialization and deserialization"
```

**Key Elements**: Library + data structure + transformation/operation

---

## Advanced Techniques

### Technique 1: Layered Specificity

Start broad, then narrow based on results:

**Layer 1** (Broad): `"authentication"`
- Result: 200 files

**Layer 2** (Narrower): `"user authentication with sessions"`
- Result: 45 files

**Layer 3** (Specific): `"user authentication with session cookies and Redis storage"`
- Result: 8 files (exactly what you need!)

### Technique 2: Negative Context (Mental Filter)

You can't use NOT operators, but you can be specific to exclude:

**Instead of**: `"authentication NOT OAuth"` ❌ (won't work)

**Use**: `"local username password authentication"` ✅ (implicitly excludes OAuth)

### Technique 3: Multi-Concept Queries

Combine multiple concepts when looking for specific intersections:

```
✅ "asynchronous database query with connection pooling and error retry"
✅ "React form component with validation, submission, and loading states"
✅ "file upload with virus scanning, format validation, and S3 storage"
```

**Why This Works**: Semantic search understands that you want code implementing ALL these concepts together.

### Technique 4: Action + Technology + Pattern

The most reliable formula:

```
[What it does] + [Using what technology] + [Following which pattern]

Examples:
✅ "rate limiting using Redis with sliding window algorithm"
✅ "authentication using JWT with refresh token rotation"
✅ "caching using Memcached with cache-aside pattern"
```

### Technique 5: Use Examples as Queries

If you found one good example, describe it to find similar code:

**You found**: Payment processing with Stripe in `checkout.js`

**Query**: `"payment processing with Stripe credit card tokenization"`

**Result**: Finds all similar payment implementations, even if they use different variable names or file structures.

---

## Query Debugging

### Problem: Too Many Results (>50)

**Diagnosis**: Query too generic

**Solutions**:
1. Add technology specificity: `"validation"` → `"email validation with regex"`
2. Add context: `"error handling"` → `"error handling in API requests"`
3. Add implementation detail: `"caching"` → `"caching with TTL expiration"`

### Problem: Too Few Results (<3)

**Diagnosis**: Query too specific or using wrong terminology

**Solutions**:
1. Remove implementation details: `"Redis cache with LRU eviction"` → `"cache with automatic expiration"`
2. Use more generic terms: `"JWT authentication"` → `"token-based authentication"`
3. Try synonyms: `"authorization"` vs `"permissions"` vs `"access control"`

### Problem: Wrong Results (Irrelevant matches)

**Diagnosis**: Query matches conceptually but wrong context

**Solutions**:
1. Add constraining context: `"user profile"` → `"user profile editing form component"`
2. Specify the layer: `"API calls"` → `"frontend API calls to backend"`
3. Be explicit about what NOT to include: Instead of `"search"`, use `"semantic code search functionality"` (excludes UI search bars)

### Problem: Missing Known Code

**Diagnosis**: Code exists but query doesn't match its semantic representation

**Solutions**:
1. Check how the code is actually structured (Read the file)
2. Query based on actual patterns: If it's class-based, mention "class"; if functional, mention "function"
3. Use the code's own terminology: Read comments/docstrings, query with those terms

---

## Quick Reference Cheat Sheet

| Goal | Weak Query | Strong Query |
|------|------------|--------------|
| Find auth | `"auth"` | `"user authentication with JWT tokens"` |
| Find DB queries | `"database"` | `"SQL query with JOIN and WHERE filtering"` |
| Find error handling | `"error"` | `"try-catch block with custom error logging"` |
| Find API calls | `"API"` | `"HTTP POST request with JSON payload"` |
| Find validation | `"validate"` | `"email format validation with regex pattern"` |
| Find caching | `"cache"` | `"Redis caching with TTL expiration"` |
| Find tests | `"test"` | `"unit test with mocked database dependencies"` |
| Find config | `"config"` | `"environment variable configuration loading"` |

---

## Practice Exercises

Test your query formulation skills:

**Exercise 1**: You want to find all places where the app sends emails.
- ❌ Weak: `"email"`
- ✅ Strong: `"email sending with SMTP server"`

**Exercise 2**: You want to find pagination logic.
- ❌ Weak: `"pagination"`
- ✅ Strong: `"page-based pagination with limit and offset"`

**Exercise 3**: You want to find where files are uploaded.
- ❌ Weak: `"upload"`
- ✅ Strong: `"file upload handling with multipart form data"`

**Exercise 4**: You want to find logging implementations.
- ❌ Weak: `"log"`
- ✅ Strong: `"structured JSON logging with log levels"`

---

**Next Steps**:
- Start with simple queries using the formulas above
- Analyze your results to understand what the search found
- Refine queries iteratively using layered specificity
- Consult `troubleshooting.md` if you encounter issues
