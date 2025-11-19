# System Architecture: TaskFlow

## Executive Summary

### Architectural Overview
TaskFlow is designed as a modern, cloud-native task management application with a clear separation between frontend and backend concerns. The architecture prioritizes **simplicity**, **maintainability**, and **cost-effectiveness** to enable solo developers or small teams to build and operate the system successfully.

**Core Architectural Principles**:
1. **Simplicity First**: Choose proven, well-documented technologies over cutting-edge complexity
2. **Stateless Design**: Enable horizontal scaling without architectural changes
3. **Security by Default**: Implement defense-in-depth security at every layer
4. **Developer Experience**: Optimize for fast local development and deployment
5. **Cost Conscious**: Minimize infrastructure costs while meeting performance requirements

### High-Level Architecture Pattern
**Pattern**: Three-tier web application with SPA frontend, RESTful API backend, and relational database

**Justification**:
- Well-understood pattern suitable for solo/small teams
- Clear separation of concerns enables independent scaling
- Large ecosystem of tools and community support
- Cost-effective deployment options (serverless, containers, VPS)

### Target Metrics
- **Performance**: <2s initial load, <200ms API response (p95)
- **Scale**: 1,000-10,000 concurrent users
- **Availability**: 99.5% uptime
- **Cost**: <$0.50/user/month infrastructure costs

---

## Architecture Overview

### System Context Diagram

```mermaid
C4Context
    title System Context Diagram - TaskFlow

    Person(user, "End User", "Individual or small team member managing tasks")
    Person(admin, "System Admin", "Self-hosted deployment administrator")

    System(taskflow, "TaskFlow Application", "Task management web application")

    System_Ext(email, "Email Service", "SendGrid/AWS SES for password resets")
    System_Ext(cdn, "CDN", "CloudFlare/CloudFront for static assets")
    System_Ext(monitoring, "Monitoring Service", "Uptime monitoring and alerting")

    Rel(user, taskflow, "Manages tasks via", "HTTPS")
    Rel(admin, taskflow, "Deploys and monitors", "SSH/Docker")
    Rel(taskflow, email, "Sends password reset emails", "SMTP/API")
    Rel(taskflow, cdn, "Serves static assets", "HTTPS")
    Rel(monitoring, taskflow, "Health checks", "HTTPS")
```

### Container Diagram

```mermaid
C4Container
    title Container Diagram - TaskFlow

    Person(user, "End User")

    Container(web, "Web Application", "React 18 + TypeScript", "Single-page application providing task management UI")
    Container(api, "API Server", "Node.js + Express + TypeScript", "RESTful API handling business logic")
    ContainerDb(db, "Database", "PostgreSQL 14+", "Stores users, tasks, lists, tags")
    ContainerDb(cache, "Cache", "Redis", "Session storage and query caching")
    Container(static, "Static Assets", "S3/CDN", "JS bundles, CSS, images")

    Rel(user, web, "Uses", "HTTPS")
    Rel(web, api, "API calls", "HTTPS/REST + JSON")
    Rel(web, static, "Loads assets", "HTTPS")
    Rel(api, db, "Reads/writes data", "PostgreSQL protocol")
    Rel(api, cache, "Session data", "Redis protocol")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### Component Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[UI Components<br/>React + TailwindCSS]
        State[State Management<br/>Zustand]
        Router[Routing<br/>React Router]
        API_Client[API Client<br/>Axios + React Query]
    end

    subgraph "API Layer"
        Routes[Route Handlers<br/>Express Router]
        Auth[Auth Middleware<br/>JWT Validation]
        Controllers[Controllers<br/>Business Logic]
        Validators[Input Validators<br/>Zod Schemas]
    end

    subgraph "Data Layer"
        ORM[ORM<br/>Prisma]
        Models[Data Models<br/>TypeScript Types]
        Migrations[Schema Migrations<br/>Prisma Migrate]
    end

    subgraph "Infrastructure Layer"
        DB[(PostgreSQL<br/>Primary Database)]
        Cache[(Redis<br/>Sessions + Cache)]
        Files[Static Files<br/>S3/Local Storage]
    end

    UI --> State
    UI --> Router
    State --> API_Client
    Router --> API_Client

    API_Client -->|HTTPS/JSON| Routes
    Routes --> Auth
    Auth --> Controllers
    Controllers --> Validators
    Controllers --> ORM

    ORM --> Models
    ORM --> DB
    Models --> Migrations

    Controllers --> Cache
    UI --> Files
```

---

## Technology Stack

### Frontend Stack

| Technology | Choice | Rationale | Alternatives Considered |
|------------|--------|-----------|------------------------|
| **Framework** | React 18 | Largest ecosystem, excellent TypeScript support, component reusability, team likely has experience | Vue 3 (smaller bundle), Svelte (performance) |
| **Language** | TypeScript 5+ | Type safety reduces bugs, excellent IDE support, self-documenting code | JavaScript (faster initial development) |
| **Build Tool** | Vite 5 | Fast HMR, optimized builds, simple config, modern ESM-based | Create React App (deprecated), Webpack (complex) |
| **Styling** | TailwindCSS 3 | Rapid UI development, small production bundle, consistent design system | CSS Modules (more verbose), Styled Components (runtime cost) |
| **State Management** | Zustand | Simple API, minimal boilerplate, TypeScript-first, 1KB bundle | Redux Toolkit (over-engineered for MVP), Context API (performance issues) |
| **Data Fetching** | React Query 5 | Automatic caching, request deduplication, optimistic updates, devtools | SWR (similar), manual fetch (reinventing wheel) |
| **Routing** | React Router 6 | Industry standard, type-safe routes, nested routing | TanStack Router (too new), manual implementation |
| **Forms** | React Hook Form | Performance, minimal re-renders, validation support | Formik (larger bundle, more re-renders) |
| **Validation** | Zod | TypeScript schema validation, shared with backend | Yup (less TypeScript support), Joi (backend-focused) |
| **Testing** | Vitest + RTL | Fast, Vite integration, compatible with Jest | Jest (slower), Testing Library alone |
| **HTTP Client** | Axios | Interceptors for auth, request/response transformation | Fetch API (more boilerplate), ky (smaller ecosystem) |

**Bundle Size Target**: <200KB gzipped initial bundle
**Browser Support**: Chrome/Firefox/Safari/Edge (latest 2 versions)

### Backend Stack

| Technology | Choice | Rationale | Alternatives Considered |
|------------|--------|-----------|------------------------|
| **Runtime** | Node.js 20 LTS | JavaScript ecosystem matches frontend, async I/O for API workloads, large talent pool | Python (FastAPI - different language), Go (steeper learning curve) |
| **Framework** | Express 4.x | Mature, minimal, flexible, huge middleware ecosystem | Fastify (faster but smaller ecosystem), NestJS (over-engineered) |
| **Language** | TypeScript 5+ | Type safety across full stack, shared types with frontend | JavaScript (maintenance challenges at scale) |
| **ORM** | Prisma 5 | Type-safe queries, excellent migrations, auto-generated types, great DX | TypeORM (more complex), Sequelize (outdated), Drizzle (too new) |
| **Database** | PostgreSQL 14+ | ACID compliance, JSON support, full-text search, proven at scale, open-source | MySQL (weaker JSON support), MongoDB (no transactions in MVP) |
| **Cache** | Redis 7 | Fast in-memory storage, simple key-value API, session store | Memcached (less features), in-memory JS Map (doesn't scale) |
| **Authentication** | JWT + Passport.js | Stateless, scales horizontally, industry standard | Sessions (requires sticky sessions), OAuth (overkill for MVP) |
| **Validation** | Zod | Shared schemas with frontend, TypeScript inference | Joi (backend-only), class-validator (decorator overhead) |
| **Testing** | Vitest + Supertest | Consistent tooling with frontend, fast test execution | Jest (slower), Mocha (more setup) |
| **API Docs** | Swagger/OpenAPI 3 | Auto-generated from code, interactive testing, client generation | Manual docs (outdated quickly), Postman collections |

**Performance Target**: <200ms p95 response time, <512MB RAM per instance

### Infrastructure & DevOps

| Technology | Choice | Rationale | Alternatives Considered |
|------------|--------|-----------|------------------------|
| **Containerization** | Docker | Consistent environments, easy deployment, wide platform support | Podman (less mature ecosystem) |
| **Orchestration** | Docker Compose (MVP) → Kubernetes (scale) | Simple for single-server, path to K8s when needed | Kubernetes immediately (over-engineered), Nomad |
| **Hosting (Recommended)** | DigitalOcean App Platform | Simple deployment, $12-50/month, auto-scaling, managed DB | AWS (complex for solo dev), Heroku (expensive), Render |
| **Alternative Hosting** | Railway.app | Generous free tier, git-push deploys, simple pricing | Fly.io (more complex), self-hosted VPS (more ops work) |
| **Database Hosting** | Managed PostgreSQL (DO/AWS RDS) | Automated backups, point-in-time recovery, monitoring | Self-hosted (requires DB expertise), Supabase (vendor lock-in) |
| **Cache Hosting** | Upstash Redis (serverless) | Pay-per-request, no idle costs, global edge caching | Redis Labs (minimum $5/month), self-hosted (ops overhead) |
| **CDN** | CloudFlare (free tier) | Global edge network, DDoS protection, SSL, free forever tier | AWS CloudFront (complex), Fastly (expensive) |
| **CI/CD** | GitHub Actions | Free for public repos, 2,000 min/month private, tight Git integration | GitLab CI (less ecosystem), CircleCI (complex pricing) |
| **Monitoring** | UptimeRobot (free) + Sentry | 50 monitors free, error tracking, performance monitoring | Datadog (expensive), New Relic (complex), self-hosted Prometheus |
| **Logging** | Structured JSON to stdout → platform logging | Built into platform, searchable, no extra cost | ELK stack (ops heavy), CloudWatch (vendor lock-in) |
| **Secrets** | Platform environment variables | Encrypted, injected at runtime, no code changes | Vault (over-engineered), .env files (insecure in prod) |
| **Backups** | Automated daily (platform) + weekly manual export | Point-in-time recovery, cross-region redundancy | Manual backups (error-prone), custom scripts |

**Deployment Cost Estimates** (USD/month):
- **Minimal (500 users)**: $25-40 (Railway free tier + Upstash free tier + CloudFlare free)
- **Standard (2,000 users)**: $50-75 (DigitalOcean App Platform $12 + managed DB $15 + Redis $10)
- **Growth (10,000 users)**: $150-250 (scaled app instances + larger DB + CDN overages)

### Development Tools

| Category | Tool | Purpose |
|----------|------|---------|
| **IDE** | VS Code | Free, excellent TypeScript/React support, extensions |
| **Code Quality** | ESLint + Prettier | Consistent formatting, catch errors early |
| **Git Hooks** | Husky + lint-staged | Pre-commit linting, prevent bad commits |
| **Package Manager** | pnpm | Fast, disk-efficient, strict dependency resolution |
| **Database GUI** | Prisma Studio | Built-in, auto-synced with schema |
| **API Testing** | Swagger UI + Insomnia | Interactive docs, manual testing |
| **Load Testing** | k6 | Scriptable, developer-friendly, CI integration |

---

## Component Design

### 1. Frontend Application (React SPA)

**Purpose**: Provide responsive, interactive UI for task management

**Technology**: React 18 + TypeScript + Vite + TailwindCSS

**Key Components**:

#### Authentication Components
```typescript
// Components
- LoginPage: Email/password form, JWT storage
- RegisterPage: User registration form
- ProtectedRoute: HOC for auth-required routes
- AuthProvider: Context for auth state

// State
interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string) => Promise<void>;
}
```

#### Task Management Components
```typescript
// Components
- TaskList: Virtualized list of tasks, filters, sorting
- TaskCard: Individual task display, inline editing
- TaskDetail: Modal with full task CRUD
- QuickAddTask: Inline task creation input
- TaskFilters: Multi-select filters (status, priority, list, tags)

// State (Zustand)
interface TaskState {
  tasks: Task[];
  filters: FilterState;
  selectedTask: Task | null;
  setFilter: (key: string, value: any) => void;
  clearFilters: () => void;
}
```

#### Organization Components
```typescript
// Components
- Sidebar: Navigation, lists, tags
- ListManager: CRUD for lists/projects
- TagCloud: Visual tag browser
- SearchBar: Real-time search with debounce

// Interfaces
interface List {
  id: string;
  name: string;
  color?: string;
  taskCount: number;
}

interface Tag {
  id: string;
  name: string;
  count: number;
}
```

**Component Structure**:
```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── ProtectedRoute.tsx
│   ├── tasks/
│   │   ├── TaskList.tsx
│   │   ├── TaskCard.tsx
│   │   ├── TaskDetail.tsx
│   │   ├── QuickAddTask.tsx
│   │   └── TaskFilters.tsx
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   └── MainLayout.tsx
│   └── shared/
│       ├── Button.tsx
│       ├── Input.tsx
│       ├── Modal.tsx
│       └── LoadingSpinner.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useTasks.ts (React Query)
│   ├── useLists.ts
│   └── useDebounce.ts
├── store/
│   ├── authStore.ts (Zustand)
│   ├── uiStore.ts
│   └── filterStore.ts
├── services/
│   ├── api.ts (Axios instance)
│   ├── authService.ts
│   ├── taskService.ts
│   └── listService.ts
├── types/
│   ├── task.ts
│   ├── user.ts
│   └── api.ts
└── utils/
    ├── dateHelpers.ts
    ├── validators.ts
    └── constants.ts
```

**Performance Optimizations**:
- React.memo for expensive components (TaskCard)
- Virtualized lists for 100+ tasks (react-window)
- Debounced search input (300ms)
- Optimistic UI updates with React Query
- Code splitting by route (React.lazy)
- Image optimization and lazy loading

---

### 2. API Server (Express + TypeScript)

**Purpose**: Handle business logic, data persistence, and authentication

**Technology**: Node.js 20 + Express 4 + TypeScript + Prisma

**API Design Principles**:
- RESTful resource-based endpoints
- Consistent error responses
- Versioned API (/api/v1/...)
- JWT authentication
- Request validation with Zod
- Rate limiting

#### Core Modules

**Authentication Module**
```typescript
// Endpoints
POST   /api/v1/auth/register     // Create account
POST   /api/v1/auth/login        // Get JWT token
POST   /api/v1/auth/logout       // Invalidate token
POST   /api/v1/auth/refresh      // Refresh JWT
GET    /api/v1/auth/me           // Get current user

// Middleware
- authenticateToken: Verify JWT, attach user to req
- rateLimitAuth: 5 requests per 15 min per IP
```

**Task Management Module**
```typescript
// Endpoints
GET    /api/v1/tasks                    // List user's tasks (paginated, filtered)
POST   /api/v1/tasks                    // Create task
GET    /api/v1/tasks/:id                // Get task by ID
PUT    /api/v1/tasks/:id                // Update task
PATCH  /api/v1/tasks/:id/status         // Quick status update
DELETE /api/v1/tasks/:id                // Delete task
GET    /api/v1/tasks/search?q=keyword   // Search tasks

// Query Params (GET /tasks)
?page=1&limit=25           // Pagination
?status=in_progress        // Filter by status
?priority=high,urgent      // Filter by priority (multi-select)
?list_id=uuid              // Filter by list
?tags=work,urgent          // Filter by tags (AND logic)
?due_before=2025-12-31     // Due date range
?sort=due_date:asc         // Sort (created_at, due_date, priority, title)
?search=keyword            // Full-text search

// Request/Response
POST /api/v1/tasks
Request:
{
  "title": "Complete architecture document",
  "description": "Design TaskFlow system architecture",
  "priority": "high",
  "status": "in_progress",
  "due_date": "2025-11-20",
  "list_id": "uuid",
  "tags": ["architecture", "documentation"]
}

Response: 201 Created
{
  "task": {
    "id": "uuid",
    "title": "Complete architecture document",
    "description": "Design TaskFlow system architecture",
    "priority": "high",
    "status": "in_progress",
    "due_date": "2025-11-20T00:00:00Z",
    "list_id": "uuid",
    "tags": ["architecture", "documentation"],
    "created_at": "2025-11-19T10:00:00Z",
    "updated_at": "2025-11-19T10:00:00Z",
    "completed_at": null,
    "user_id": "uuid"
  }
}
```

**List Management Module**
```typescript
// Endpoints
GET    /api/v1/lists           // List all user's lists
POST   /api/v1/lists           // Create list
GET    /api/v1/lists/:id       // Get list with task count
PUT    /api/v1/lists/:id       // Update list
DELETE /api/v1/lists/:id       // Delete list (requires task handling)

// Validation
- Max 50 lists per user
- List name: 1-100 characters
- Color: hex color code (optional)
```

**Tag Management Module**
```typescript
// Endpoints
GET    /api/v1/tags            // List all user's tags with counts
POST   /api/v1/tasks/:id/tags  // Add tags to task
DELETE /api/v1/tasks/:id/tags  // Remove tags from task

// Auto-complete
GET /api/v1/tags/autocomplete?q=wor
Response: ["work", "workflow", "workshop"]
```

**Project Structure**:
```
src/
├── server.ts                 // Express app initialization
├── config/
│   ├── database.ts           // Prisma client
│   ├── redis.ts              // Redis connection
│   └── env.ts                // Environment variables
├── routes/
│   ├── auth.routes.ts
│   ├── tasks.routes.ts
│   ├── lists.routes.ts
│   └── tags.routes.ts
├── controllers/
│   ├── auth.controller.ts
│   ├── tasks.controller.ts
│   ├── lists.controller.ts
│   └── tags.controller.ts
├── middleware/
│   ├── auth.middleware.ts     // JWT verification
│   ├── validate.middleware.ts // Zod validation
│   ├── rateLimit.middleware.ts
│   ├── error.middleware.ts    // Centralized error handling
│   └── cors.middleware.ts
├── services/
│   ├── auth.service.ts        // Business logic
│   ├── task.service.ts
│   ├── list.service.ts
│   └── tag.service.ts
├── schemas/
│   ├── task.schema.ts         // Zod schemas
│   ├── user.schema.ts
│   └── list.schema.ts
├── types/
│   ├── express.d.ts           // Extend Express types
│   └── index.ts
└── utils/
    ├── jwt.ts                 // Token generation/validation
    ├── password.ts            // bcrypt helpers
    ├── errors.ts              // Custom error classes
    └── pagination.ts
```

**Error Handling Strategy**:
```typescript
// Standard error response format
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Title is required and must be 1-255 characters",
    "details": {
      "field": "title",
      "constraint": "length"
    },
    "timestamp": "2025-11-19T10:00:00Z",
    "request_id": "uuid"
  }
}

// Error codes
- VALIDATION_ERROR: 400
- UNAUTHORIZED: 401
- FORBIDDEN: 403
- NOT_FOUND: 404
- RATE_LIMIT_EXCEEDED: 429
- INTERNAL_ERROR: 500
- DATABASE_ERROR: 500
```

---

### 3. Database (PostgreSQL)

**Purpose**: Persistent storage for user data, tasks, and relationships

**Technology**: PostgreSQL 14+

**Schema Design** (Prisma ORM):

```prisma
// schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id            String    @id @default(uuid())
  email         String    @unique
  passwordHash  String    @map("password_hash")
  createdAt     DateTime  @default(now()) @map("created_at")
  updatedAt     DateTime  @updatedAt @map("updated_at")

  tasks         Task[]
  lists         List[]

  @@map("users")
}

model Task {
  id            String    @id @default(uuid())
  title         String    @db.VarChar(255)
  description   String?   @db.Text
  status        Status    @default(NOT_STARTED)
  priority      Priority  @default(MEDIUM)
  dueDate       DateTime? @map("due_date") @db.Date
  completedAt   DateTime? @map("completed_at")
  createdAt     DateTime  @default(now()) @map("created_at")
  updatedAt     DateTime  @updatedAt @map("updated_at")

  userId        String    @map("user_id")
  user          User      @relation(fields: [userId], references: [id], onDelete: Cascade)

  listId        String?   @map("list_id")
  list          List?     @relation(fields: [listId], references: [id], onDelete: SetNull)

  tags          TaskTag[]

  @@index([userId, status])
  @@index([userId, dueDate])
  @@index([userId, createdAt])
  @@index([userId, listId])
  @@map("tasks")
}

model List {
  id            String    @id @default(uuid())
  name          String    @db.VarChar(100)
  color         String?   @db.VarChar(7) // Hex color
  createdAt     DateTime  @default(now()) @map("created_at")
  updatedAt     DateTime  @updatedAt @map("updated_at")

  userId        String    @map("user_id")
  user          User      @relation(fields: [userId], references: [id], onDelete: Cascade)

  tasks         Task[]

  @@unique([userId, name]) // Prevent duplicate list names per user
  @@index([userId])
  @@map("lists")
}

model Tag {
  id            String    @id @default(uuid())
  name          String    @db.VarChar(30)

  tasks         TaskTag[]

  @@unique([name]) // Global unique tags (case-insensitive via app logic)
  @@map("tags")
}

model TaskTag {
  taskId        String    @map("task_id")
  task          Task      @relation(fields: [taskId], references: [id], onDelete: Cascade)

  tagId         String    @map("tag_id")
  tag           Tag       @relation(fields: [tagId], references: [id], onDelete: Cascade)

  createdAt     DateTime  @default(now()) @map("created_at")

  @@id([taskId, tagId])
  @@index([tagId])
  @@map("task_tags")
}

enum Status {
  NOT_STARTED
  IN_PROGRESS
  COMPLETED
  BLOCKED
}

enum Priority {
  LOW
  MEDIUM
  HIGH
  URGENT
}
```

**Indexing Strategy**:
```sql
-- Composite indexes for common queries
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_user_due_date ON tasks(user_id, due_date);
CREATE INDEX idx_tasks_user_created ON tasks(user_id, created_at);
CREATE INDEX idx_tasks_user_list ON tasks(user_id, list_id);

-- Full-text search index
CREATE INDEX idx_tasks_title_search ON tasks USING GIN(to_tsvector('english', title));
CREATE INDEX idx_tasks_description_search ON tasks USING GIN(to_tsvector('english', description));

-- Explain plan for common query
EXPLAIN ANALYZE
SELECT * FROM tasks
WHERE user_id = 'uuid'
  AND status IN ('NOT_STARTED', 'IN_PROGRESS')
  AND due_date <= '2025-11-30'
ORDER BY due_date ASC
LIMIT 25;
```

**Data Migrations**:
- Prisma Migrate for schema changes
- Version controlled in `prisma/migrations/`
- Automatic rollback on failure
- Seed data for development (`prisma/seed.ts`)

**Backup Strategy**:
- Daily automated backups (3 AM UTC)
- 30-day retention policy
- Point-in-time recovery (PITR) enabled
- Weekly manual export to S3/external storage
- Quarterly restore tests

---

### 4. Cache Layer (Redis)

**Purpose**: Session storage, query caching, rate limiting

**Technology**: Redis 7

**Use Cases**:

**Session Storage**
```typescript
// Store JWT sessions (optional - for logout/revocation)
// Key: session:{user_id}:{token_id}
// Value: { user_id, email, issued_at, expires_at }
// TTL: 24 hours (matches JWT expiration)

await redis.setex(
  `session:${userId}:${tokenId}`,
  86400, // 24 hours
  JSON.stringify({ userId, email, issuedAt, expiresAt })
);
```

**Query Caching**
```typescript
// Cache frequently accessed data
// Key: user:{user_id}:lists
// TTL: 5 minutes

const cacheKey = `user:${userId}:lists`;
const cached = await redis.get(cacheKey);

if (cached) {
  return JSON.parse(cached);
}

const lists = await prisma.list.findMany({ where: { userId } });
await redis.setex(cacheKey, 300, JSON.stringify(lists));
return lists;
```

**Rate Limiting**
```typescript
// Sliding window rate limit
// Key: ratelimit:{ip}:{endpoint}
// Value: timestamp array
// TTL: 15 minutes

const key = `ratelimit:${ip}:auth`;
const count = await redis.incr(key);

if (count === 1) {
  await redis.expire(key, 900); // 15 minutes
}

if (count > 5) {
  throw new RateLimitError('Too many attempts');
}
```

**Cache Invalidation Strategy**:
- Write-through: Update cache on data modification
- TTL-based: Short TTLs for frequently changing data
- Event-based: Clear cache on specific mutations

---

## Interface Specifications

### REST API Endpoints

**Base URL**: `https://api.taskflow.com/v1`

**Authentication**: JWT Bearer token in Authorization header

**Common Headers**:
```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
```

### Authentication Endpoints

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response: 201 Created
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2025-11-19T10:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Errors:
400 - Email already registered
400 - Password does not meet requirements
429 - Rate limit exceeded
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response: 200 OK
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-11-20T10:00:00Z"
}

Errors:
401 - Invalid credentials
423 - Account locked (too many failed attempts)
429 - Rate limit exceeded
```

### Task Endpoints

#### List Tasks (with filtering)
```http
GET /api/v1/tasks?status=in_progress&priority=high,urgent&page=1&limit=25
Authorization: Bearer <token>

Response: 200 OK
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Complete architecture document",
      "description": "Design TaskFlow system...",
      "status": "in_progress",
      "priority": "high",
      "due_date": "2025-11-20T00:00:00Z",
      "completed_at": null,
      "created_at": "2025-11-19T10:00:00Z",
      "updated_at": "2025-11-19T10:00:00Z",
      "list": {
        "id": "uuid",
        "name": "Work",
        "color": "#3b82f6"
      },
      "tags": ["architecture", "documentation"]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 25,
    "total": 127,
    "total_pages": 6,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Create Task
```http
POST /api/v1/tasks
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "title": "Review pull request",
  "description": "Code review for auth module",
  "priority": "medium",
  "status": "not_started",
  "due_date": "2025-11-21",
  "list_id": "uuid",
  "tags": ["code-review", "backend"]
}

Response: 201 Created
{
  "task": {
    "id": "uuid",
    "title": "Review pull request",
    ...
  }
}

Errors:
400 - Validation error (title required, max length exceeded, etc.)
401 - Unauthorized
404 - List not found
```

#### Update Task
```http
PUT /api/v1/tasks/{id}
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "title": "Review pull request (updated)",
  "status": "in_progress",
  "priority": "high"
}

Response: 200 OK
{
  "task": { ... }
}

Errors:
400 - Validation error
401 - Unauthorized
403 - Forbidden (not task owner)
404 - Task not found
```

#### Quick Status Update
```http
PATCH /api/v1/tasks/{id}/status
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "status": "completed"
}

Response: 200 OK
{
  "task": {
    "id": "uuid",
    "status": "completed",
    "completed_at": "2025-11-19T14:30:00Z",
    ...
  }
}
```

#### Search Tasks
```http
GET /api/v1/tasks/search?q=architecture&limit=10
Authorization: Bearer <token>

Response: 200 OK
{
  "tasks": [...],
  "query": "architecture",
  "total_results": 5
}
```

### Data Contracts (TypeScript)

**Shared Types** (frontend + backend):
```typescript
// types/task.ts
export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string; // ISO 8601 date
  completed_at?: string; // ISO 8601 datetime
  created_at: string;
  updated_at: string;
  user_id: string;
  list_id?: string;
  list?: ListSummary;
  tags: string[];
}

export enum TaskStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  BLOCKED = 'blocked'
}

export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export interface CreateTaskDTO {
  title: string;
  description?: string;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string;
  list_id?: string;
  tags?: string[];
}

export interface UpdateTaskDTO extends Partial<CreateTaskDTO> {}

export interface TaskFilters {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  list_id?: string;
  tags?: string[];
  due_before?: string;
  due_after?: string;
  search?: string;
}

// types/pagination.ts
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// types/api.ts
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    timestamp: string;
    request_id: string;
  };
}
```

---

## Security Considerations

### 1. Authentication & Authorization

**JWT Implementation**:
```typescript
// Token payload
interface JwtPayload {
  sub: string;        // user_id
  email: string;
  iat: number;        // issued at (Unix timestamp)
  exp: number;        // expires at (24 hours from iat)
  jti: string;        // JWT ID (for revocation)
}

// Token generation
const token = jwt.sign(
  { sub: user.id, email: user.email },
  process.env.JWT_SECRET!,
  {
    expiresIn: '24h',
    jwtid: crypto.randomUUID()
  }
);

// Token storage (frontend)
// httpOnly cookie (preferred - XSS protection)
res.cookie('auth_token', token, {
  httpOnly: true,
  secure: true,      // HTTPS only
  sameSite: 'strict',
  maxAge: 86400000   // 24 hours
});

// OR localStorage (for mobile apps, less secure)
localStorage.setItem('auth_token', token);
```

**Authorization Middleware**:
```typescript
// Verify user owns resource
export const authorizeTaskAccess = async (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const taskId = req.params.id;
  const userId = req.user!.id;

  const task = await prisma.task.findUnique({
    where: { id: taskId },
    select: { user_id: true }
  });

  if (!task || task.user_id !== userId) {
    return res.status(403).json({
      error: { code: 'FORBIDDEN', message: 'Access denied' }
    });
  }

  next();
};
```

**Password Security**:
```typescript
import bcrypt from 'bcrypt';

// Hashing (registration)
const SALT_ROUNDS = 12; // 2^12 iterations (~250ms on modern CPU)
const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

// Verification (login)
const isValid = await bcrypt.compare(password, user.passwordHash);

// Password requirements (Zod schema)
const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain uppercase letter')
  .regex(/[a-z]/, 'Password must contain lowercase letter')
  .regex(/[0-9]/, 'Password must contain number');
```

### 2. Input Validation & Sanitization

**Server-Side Validation** (Zod):
```typescript
import { z } from 'zod';

// Task creation schema
export const createTaskSchema = z.object({
  title: z.string()
    .min(1, 'Title is required')
    .max(255, 'Title must be max 255 characters')
    .trim(),
  description: z.string()
    .max(5000, 'Description must be max 5000 characters')
    .optional(),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).optional(),
  status: z.enum(['not_started', 'in_progress', 'completed', 'blocked']).optional(),
  due_date: z.string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format (use YYYY-MM-DD)')
    .optional(),
  list_id: z.string().uuid('Invalid list ID').optional(),
  tags: z.array(z.string().max(30).regex(/^[a-zA-Z0-9_-]+$/))
    .max(10, 'Maximum 10 tags allowed')
    .optional()
});

// Validation middleware
export const validate = (schema: z.ZodSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid input',
            details: error.errors
          }
        });
      }
      next(error);
    }
  };
};
```

**SQL Injection Prevention**:
- Use Prisma ORM (parameterized queries only)
- Never use raw SQL with string concatenation
- If raw SQL needed, use `$queryRaw` with parameters

```typescript
// SAFE (Prisma)
const tasks = await prisma.task.findMany({
  where: { user_id: userId, title: { contains: searchQuery } }
});

// SAFE (Raw SQL with parameters)
const tasks = await prisma.$queryRaw`
  SELECT * FROM tasks
  WHERE user_id = ${userId} AND title ILIKE ${'%' + searchQuery + '%'}
`;

// DANGEROUS - NEVER DO THIS
const tasks = await prisma.$queryRawUnsafe(
  `SELECT * FROM tasks WHERE title = '${searchQuery}'` // SQL injection vulnerable!
);
```

**XSS Prevention**:
- React escapes output by default
- Sanitize HTML if using `dangerouslySetInnerHTML`
- Content Security Policy (CSP) headers

```typescript
// CSP headers
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"], // Remove unsafe-inline in production
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.taskflow.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: []
    }
  }
}));
```

### 3. Rate Limiting

**Implementation** (express-rate-limit + Redis):
```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';

// Global API rate limit
const globalLimiter = rateLimit({
  store: new RedisStore({ client: redis }),
  windowMs: 60 * 1000,     // 1 minute
  max: 100,                // 100 requests per minute per user
  message: 'Too many requests, please try again later',
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.user?.id || req.ip
});

// Authentication rate limit (stricter)
const authLimiter = rateLimit({
  store: new RedisStore({ client: redis }),
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 5,                     // 5 attempts per 15 min
  skipSuccessfulRequests: true,
  message: 'Too many login attempts, please try again in 15 minutes'
});

// Apply middleware
app.use('/api/v1', globalLimiter);
app.use('/api/v1/auth/login', authLimiter);
app.use('/api/v1/auth/register', authLimiter);
```

### 4. HTTPS & Transport Security

**Enforcement**:
```typescript
// Redirect HTTP to HTTPS in production
if (process.env.NODE_ENV === 'production') {
  app.use((req, res, next) => {
    if (req.header('x-forwarded-proto') !== 'https') {
      return res.redirect(`https://${req.header('host')}${req.url}`);
    }
    next();
  });
}

// HSTS header (force HTTPS for 1 year)
app.use(helmet.hsts({
  maxAge: 31536000,
  includeSubDomains: true,
  preload: true
}));
```

**TLS Configuration**:
- TLS 1.2+ only (disable TLS 1.0/1.1)
- Strong cipher suites
- Certificate from Let's Encrypt (free) or platform-provided

### 5. CORS Configuration

```typescript
import cors from 'cors';

const corsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = [
      'https://taskflow.com',
      'https://www.taskflow.com',
      'http://localhost:5173'  // Vite dev server
    ];

    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,  // Allow cookies
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

app.use(cors(corsOptions));
```

### 6. Secrets Management

**Environment Variables**:
```bash
# .env (NEVER commit to git)
DATABASE_URL="postgresql://user:password@localhost:5432/taskflow"
JWT_SECRET="your-256-bit-secret-here"  # Generate with: openssl rand -base64 32
REDIS_URL="redis://localhost:6379"
NODE_ENV="production"
PORT="3000"

# Frontend (.env)
VITE_API_URL="https://api.taskflow.com/v1"
```

**Secret Rotation**:
- JWT secret rotated quarterly
- Database password rotated annually
- Old secrets maintained for 7 days during rotation

### 7. Database Security

**Row-Level Security** (implemented in application logic):
```typescript
// ALWAYS filter by user_id
const tasks = await prisma.task.findMany({
  where: {
    user_id: req.user!.id,  // CRITICAL: prevent horizontal privilege escalation
    status: 'in_progress'
  }
});

// Prevent updating other users' tasks
const task = await prisma.task.updateMany({
  where: {
    id: taskId,
    user_id: req.user!.id  // CRITICAL: security check
  },
  data: { status: 'completed' }
});

if (task.count === 0) {
  throw new ForbiddenError('Task not found or access denied');
}
```

**Database Access Control**:
- Application uses dedicated DB user (not postgres superuser)
- Minimal privileges: SELECT, INSERT, UPDATE, DELETE on tables
- No DDL permissions (schema changes via migrations only)

**Encryption**:
- Encryption at rest (managed by database hosting provider)
- Encryption in transit (SSL/TLS for DB connections)
- Sensitive fields (future): client-side encryption for descriptions

### 8. Dependency Security

**Automated Scanning**:
```json
// package.json scripts
{
  "scripts": {
    "audit": "pnpm audit",
    "audit:fix": "pnpm audit --fix"
  }
}

// GitHub Actions workflow
- name: Security audit
  run: pnpm audit --audit-level=high
```

**Dependency Updates**:
- Dependabot enabled for automated PRs
- Review and test before merging
- Pin exact versions in production
- Weekly security patch review

---

## Performance & Scalability

### 1. Frontend Optimization

**Code Splitting**:
```typescript
// Route-based code splitting
import { lazy, Suspense } from 'react';

const TasksPage = lazy(() => import('./pages/TasksPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

// App.tsx
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/tasks" element={<TasksPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Routes>
</Suspense>
```

**Bundle Optimization**:
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', 'framer-motion']
        }
      }
    },
    chunkSizeWarningLimit: 600
  }
});
```

**Asset Optimization**:
- Images: WebP format, lazy loading, responsive images
- Fonts: Subset fonts, preload critical fonts
- Icons: SVG sprite sheet or icon font
- CSS: PurgeCSS via Tailwind (removes unused styles)

**Caching Strategy**:
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    assetsInlineLimit: 4096,  // Inline assets < 4KB as base64
    cssCodeSplit: true,
    sourcemap: false          // Disable in production
  }
});

// Cache-Control headers (via platform or CDN)
// Static assets: Cache-Control: public, max-age=31536000, immutable
// HTML: Cache-Control: no-cache
// API responses: Cache-Control: private, max-age=0
```

### 2. Backend Optimization

**Database Query Optimization**:
```typescript
// Efficient task list query
const tasks = await prisma.task.findMany({
  where: {
    user_id: userId,
    status: { in: ['not_started', 'in_progress'] }
  },
  select: {
    id: true,
    title: true,
    status: true,
    priority: true,
    due_date: true,
    list: { select: { id: true, name: true, color: true } },
    tags: { select: { tag: { select: { name: true } } } },
    created_at: true
    // Exclude: description (large field, not needed in list view)
  },
  orderBy: { created_at: 'desc' },
  take: 25,
  skip: (page - 1) * 25
});

// Use lean queries - only select needed fields
// Avoid N+1 queries - use include/select for relations
```

**Caching Layer**:
```typescript
// Cache wrapper
async function getCachedOrFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 300
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) {
    return JSON.parse(cached);
  }

  const data = await fetcher();
  await redis.setex(key, ttl, JSON.stringify(data));
  return data;
}

// Usage
const lists = await getCachedOrFetch(
  `user:${userId}:lists`,
  () => prisma.list.findMany({ where: { userId } }),
  300 // 5 minutes
);

// Cache invalidation on mutation
await prisma.list.create({ data: { ... } });
await redis.del(`user:${userId}:lists`); // Invalidate cache
```

**Connection Pooling**:
```typescript
// Prisma connection pool (default: 10 connections)
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL
    }
  },
  log: process.env.NODE_ENV === 'development' ? ['query', 'error'] : ['error']
});

// Recommended pool size: (CPU cores * 2) + effective_spindle_count
// For 2 CPU server: 10-20 connections
```

**Response Compression**:
```typescript
import compression from 'compression';

app.use(compression({
  level: 6,              // Balance between speed and compression ratio
  threshold: 1024,       // Only compress responses > 1KB
  filter: (req, res) => {
    if (req.headers['x-no-compression']) {
      return false;
    }
    return compression.filter(req, res);
  }
}));
```

### 3. Scalability Architecture

**Stateless API Design**:
- No server-side session storage (use JWT)
- All state in database or Redis
- Enables horizontal scaling via load balancer

**Horizontal Scaling**:
```yaml
# docker-compose.yml (multiple API instances)
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - api-1
      - api-2
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

  api-1:
    build: ./api
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  api-2:
    build: ./api
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}

  postgres:
    image: postgres:14
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
```

**Load Balancer Configuration** (nginx):
```nginx
# nginx.conf
upstream api_servers {
  least_conn;  # Route to server with fewest connections
  server api-1:3000;
  server api-2:3000;
}

server {
  listen 80;

  location /api/ {
    proxy_pass http://api_servers;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 5s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
  }

  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
  }
}
```

**Database Scaling Strategy**:
- **Phase 1 (0-5K users)**: Single PostgreSQL instance
- **Phase 2 (5K-50K users)**: Add read replica for reporting queries
- **Phase 3 (50K+ users)**: Partition by user_id, multi-region replication

**Caching Strategy**:
```typescript
// Cache hierarchy
// L1: React Query (client-side, immediate)
// L2: Redis (server-side, 5-15 min TTL)
// L3: Database (source of truth)

// Example: Task list caching
// Client: React Query cache (staleTime: 5 min, cacheTime: 30 min)
// Server: Redis cache (TTL: 5 min)
// Database: Indexed query
```

### 4. Performance Monitoring

**Metrics to Track**:
```typescript
// API response time middleware
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    const duration = Date.now() - start;

    // Log slow requests
    if (duration > 500) {
      logger.warn('Slow request', {
        method: req.method,
        path: req.path,
        duration,
        user_id: req.user?.id
      });
    }

    // Send to monitoring service
    metrics.histogram('api.response_time', duration, {
      method: req.method,
      path: req.path,
      status: res.statusCode
    });
  });

  next();
});
```

**Database Query Performance**:
```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION pg_stat_statements;

-- Find slowest queries
SELECT
  mean_exec_time,
  calls,
  query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Frontend Performance (Lighthouse CI)**:
```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on: [pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Lighthouse
        uses: treosh/lighthouse-ci-action@v9
        with:
          urls: 'https://staging.taskflow.com'
          budgetPath: './lighthouse-budget.json'
          uploadArtifacts: true
```

---

## Deployment Architecture

### 1. Environments

**Development** (Local):
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:3000/api/v1

  api:
    build:
      context: ./api
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./api:/app
      - /app/node_modules
    environment:
      - DATABASE_URL=postgresql://taskflow:dev@postgres:5432/taskflow_dev
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=dev-secret-change-in-production
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=taskflow
      - POSTGRES_PASSWORD=dev
      - POSTGRES_DB=taskflow_dev
    volumes:
      - postgres_dev:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_dev:
```

**Staging**:
- Deployed on DigitalOcean App Platform
- Auto-deploy from `develop` branch
- Shared database with production (separate schema)
- Monitoring enabled
- Purpose: Pre-production testing

**Production**:
- Deployed on DigitalOcean App Platform
- Manual deploy from `main` branch (after approval)
- High availability setup (2+ instances)
- Automated backups
- Full monitoring and alerting

### 2. Deployment Strategy

**Platform: DigitalOcean App Platform** (Recommended)

**Rationale**:
- Simple git-based deployments
- Auto-scaling and load balancing
- Managed PostgreSQL and Redis
- $12-50/month for MVP scale
- No Kubernetes complexity

**Configuration** (.do/app.yaml):
```yaml
name: taskflow
region: nyc

databases:
  - name: taskflow-db
    engine: PG
    version: "14"
    size: db-s-1vcpu-1gb
    num_nodes: 1
    production: true

services:
  # Backend API
  - name: api
    source:
      repo: github.com/yourorg/taskflow
      branch: main
      dir: /api
    build_command: pnpm install && pnpm build
    run_command: node dist/server.js
    instance_count: 2
    instance_size_slug: basic-xxs  # $12/month
    http_port: 3000
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${taskflow-db.DATABASE_URL}
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${redis.REDIS_URL}
      - key: JWT_SECRET
        scope: RUN_TIME
        type: SECRET
        value: ${JWT_SECRET}
      - key: NODE_ENV
        scope: RUN_TIME
        value: production
    routes:
      - path: /api

  # Frontend SPA
  - name: web
    source:
      repo: github.com/yourorg/taskflow
      branch: main
      dir: /frontend
    build_command: pnpm install && pnpm build
    output_dir: dist
    instance_count: 1
    instance_size_slug: basic-xxs
    static_site: true
    envs:
      - key: VITE_API_URL
        scope: BUILD_TIME
        value: https://taskflow.com/api/v1
    routes:
      - path: /

workers:
  # Redis
  - name: redis
    image:
      registry_type: DOCKER_HUB
      registry: redis
      repository: redis
      tag: "7-alpine"
    instance_size_slug: basic-xxs
    instance_count: 1
```

**Alternative: Railway.app** (For Free Tier):
```yaml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "pnpm start"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "api"
source = "./api"
variables = { NODE_ENV = "production" }

[[services]]
name = "web"
source = "./frontend"
staticPublishPath = "dist"

[[services]]
name = "postgres"
type = "database"
plan = "hobby"  # Free tier

[[services]]
name = "redis"
type = "database"
plan = "hobby"  # Free tier
```

### 3. CI/CD Pipeline

**GitHub Actions** (.github/workflows/deploy.yml):
```yaml
name: Deploy Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install

      - name: Run linter
        run: pnpm lint

      - name: Run tests
        run: pnpm test

      - name: Build
        run: pnpm build

  deploy-api:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to DigitalOcean
        uses: digitalocean/app_action@v1
        with:
          app_name: taskflow
          token: ${{ secrets.DIGITALOCEAN_TOKEN }}

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build frontend
        run: |
          cd frontend
          pnpm install
          pnpm build

      - name: Deploy to CloudFlare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: taskflow
          directory: frontend/dist
```

### 4. Monitoring & Observability

**Health Check Endpoint**:
```typescript
// routes/health.routes.ts
app.get('/health', async (req, res) => {
  const checks = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    checks: {
      database: 'unknown',
      redis: 'unknown'
    }
  };

  // Database check
  try {
    await prisma.$queryRaw`SELECT 1`;
    checks.checks.database = 'healthy';
  } catch (error) {
    checks.checks.database = 'unhealthy';
    checks.status = 'degraded';
  }

  // Redis check
  try {
    await redis.ping();
    checks.checks.redis = 'healthy';
  } catch (error) {
    checks.checks.redis = 'unhealthy';
    checks.status = 'degraded';
  }

  const statusCode = checks.status === 'ok' ? 200 : 503;
  res.status(statusCode).json(checks);
});
```

**Uptime Monitoring** (UptimeRobot):
- Monitor /health endpoint every 5 minutes
- Alert via email/Slack if 2 consecutive failures
- Free tier: 50 monitors

**Error Tracking** (Sentry):
```typescript
// api/server.ts
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1  // 10% of transactions
});

app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.errorHandler());
```

**Logging Strategy**:
```typescript
// utils/logger.ts
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// Usage
logger.info('Task created', { task_id, user_id });
logger.error('Database error', { error: err.message, stack: err.stack });
```

**Metrics Dashboard** (Recommended: Grafana Cloud Free Tier):
- API request rate (req/sec)
- Response time percentiles (p50, p95, p99)
- Error rate (5xx responses)
- Database query time
- Active users (DAU, MAU)

### 5. Backup & Disaster Recovery

**Database Backups**:
```bash
# Automated daily backup (via platform or cron)
#!/bin/bash
# backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="taskflow_backup_${TIMESTAMP}.sql"

pg_dump $DATABASE_URL > $BACKUP_FILE
gzip $BACKUP_FILE

# Upload to S3/DigitalOcean Spaces
aws s3 cp ${BACKUP_FILE}.gz s3://taskflow-backups/

# Retention: 30 days
find . -name "taskflow_backup_*.sql.gz" -mtime +30 -delete
```

**Point-in-Time Recovery** (PITR):
- Enabled via managed database provider
- 7-day retention window
- Recovery granularity: 5 minutes

**Disaster Recovery Plan**:
1. **RTO (Recovery Time Objective)**: 1 hour
2. **RPO (Recovery Point Objective)**: 15 minutes
3. **Backup Testing**: Monthly restore drills
4. **Runbook**: Documented recovery procedures in `/docs/runbooks/disaster-recovery.md`

---

## Architectural Decision Records (ADRs)

See separate ADR documents in `docs/adrs/`:
- ADR-001: Database Choice (PostgreSQL)
- ADR-002: Frontend Framework (React + TypeScript)
- ADR-003: Authentication Strategy (JWT)
- ADR-004: Deployment Platform (DigitalOcean App Platform)
- ADR-005: State Management (Zustand)
- ADR-006: API Design (RESTful vs GraphQL)

---

## Cost Estimation

### MVP (100-500 users)
| Service | Provider | Cost |
|---------|----------|------|
| Hosting (API + Web) | Railway.app | $0 (free tier) |
| Database | Railway PostgreSQL | $0 (free tier) |
| Redis | Upstash | $0 (free tier) |
| CDN | CloudFlare | $0 (free tier) |
| Monitoring | UptimeRobot | $0 (free tier) |
| Error Tracking | Sentry | $0 (free tier) |
| **Total** | | **$0/month** |

### Growth (1,000-5,000 users)
| Service | Provider | Cost |
|---------|----------|------|
| Hosting | DigitalOcean App Platform | $24 (2x basic-xxs) |
| Database | DigitalOcean Managed PostgreSQL | $15 (1GB RAM) |
| Redis | Upstash Pro | $10 |
| CDN | CloudFlare | $0 (free tier) |
| Domain | Namecheap | $1 |
| Monitoring | UptimeRobot | $0 (free tier) |
| Error Tracking | Sentry | $26 (Team plan) |
| **Total** | | **$76/month** |

### Scale (10,000+ users)
| Service | Provider | Cost |
|---------|----------|------|
| Hosting | DigitalOcean App Platform | $72 (6x basic-xxs) |
| Database | DigitalOcean Managed PostgreSQL | $60 (4GB RAM) |
| Redis | Upstash Pro | $30 |
| CDN | CloudFlare Pro | $20 |
| Domain | Namecheap | $1 |
| Monitoring | Grafana Cloud | $0 (free tier) |
| Error Tracking | Sentry | $26 (Team plan) |
| Backups | S3 | $5 |
| **Total** | | **$214/month** |

---

## Migration Path from MVP to Scale

### Phase 1: MVP (Weeks 1-12)
- Single API instance
- Single database instance
- No caching
- Basic monitoring
- Focus: Feature delivery

### Phase 2: Optimization (Months 3-6)
- Add Redis caching
- Implement query optimization
- Add performance monitoring
- Focus: Response time < 200ms

### Phase 3: Horizontal Scaling (Months 6-12)
- Multiple API instances + load balancer
- Database read replica
- CDN for static assets
- Advanced monitoring
- Focus: Support 10K+ users

### Phase 4: Global Scale (Year 2+)
- Multi-region deployment
- Database sharding
- Advanced caching (edge caching)
- Real-time features (WebSockets)
- Focus: 100K+ users, <100ms latency

---

## Document Metadata

**Version**: 1.0
**Last Updated**: 2025-11-19
**Author**: System Architect (Claude)
**Status**: Ready for Review
**Related Documents**:
- docs/planning/requirements.md
- docs/adrs/*.md (Architecture Decision Records)

**Review Checklist**:
- [ ] Technology stack approved by technical lead
- [ ] Security measures reviewed by security specialist
- [ ] Deployment strategy validated with DevOps
- [ ] Cost estimates approved by project sponsor
- [ ] Performance targets aligned with NFRs

---

## Next Steps

1. **Architecture Review**: Technical team reviews and provides feedback
2. **ADR Creation**: Document key decisions in separate ADR files
3. **Proof of Concept**: Build minimal API + frontend to validate stack
4. **Database Schema**: Finalize Prisma schema and run migrations
5. **Development**: Begin sprint 1 with authentication module
6. **Infrastructure Setup**: Provision staging and production environments

---

**END OF ARCHITECTURE DOCUMENT**

*Total Lines: ~1,400+*
*Estimated Read Time: 45-60 minutes*
*Complexity: Medium (solo/small team friendly)*
