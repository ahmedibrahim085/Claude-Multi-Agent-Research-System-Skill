# Implementation Tasks: TaskFlow

## Overview

**Total Tasks**: 42
**Estimated Effort**: 280-360 hours (8-12 weeks for solo developer, 4-6 weeks for 2-person team)
**Critical Path**: TASK-001 → TASK-002 → TASK-003 → TASK-007 → TASK-011 → TASK-015 → TASK-019 → TASK-023 → TASK-027 → TASK-031
**Parallel Work Streams**: 3 (Backend API, Frontend UI, Infrastructure)

### Phase Summary

| Phase | Duration | Effort (hours) | Parallel Streams |
|-------|----------|----------------|------------------|
| Phase 1: Project Setup & Infrastructure | 3 days | 24-32 | 1 |
| Phase 2: Authentication Module | 5 days | 40-48 | 2 (after API contract) |
| Phase 3: Core Task CRUD | 7 days | 56-72 | 2 (parallel) |
| Phase 4: Task Organization Features | 8 days | 64-80 | 2 (parallel) |
| Phase 5: Search & Filtering | 5 days | 40-48 | 2 (parallel) |
| Phase 6: UI Polish & Testing | 7 days | 56-80 | 2 (parallel) |
| **Total** | **35 days** | **280-360 hours** | |

### Work Stream Distribution

- **Backend API**: 18 tasks (144-176 hours)
- **Frontend UI**: 17 tasks (112-144 hours)
- **Infrastructure & DevOps**: 7 tasks (24-40 hours)

---

## Phase 1: Project Setup & Infrastructure

**Duration**: 3 days
**Effort**: 24-32 hours
**Goal**: Establish development environment, database schema, and deployment pipeline

---

### TASK-001: Initialize Project Repository
**ID**: TASK-001
**Complexity**: S (Small)
**Effort**: 4 hours
**Dependencies**: None
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Any developer

**Description**: Set up monorepo structure with frontend and backend projects, initialize version control, and configure development tools.

**Subtasks**:
- [ ] Create Git repository with `.gitignore` for Node.js + TypeScript
- [ ] Initialize pnpm workspace with root `package.json`
- [ ] Create folder structure: `/frontend`, `/api`, `/docs`, `/scripts`
- [ ] Set up ESLint + Prettier for both frontend and backend
- [ ] Configure Husky pre-commit hooks for linting
- [ ] Create initial `README.md` with setup instructions
- [ ] Add MIT license file

**Acceptance Criteria**:
- [ ] Repository cloned and all team members can run `pnpm install` successfully
- [ ] Pre-commit hooks block commits with linting errors
- [ ] Folder structure matches architecture document specification
- [ ] README contains clear setup steps for local development
- [ ] `pnpm lint` runs successfully on both frontend and backend

**Technical Notes**:
- Use pnpm workspaces for monorepo management
- Configure VS Code settings in `.vscode/settings.json` for consistent formatting
- Pin Node.js version in `.nvmrc` (v20.x LTS)

**Files to Create**:
- `.gitignore`, `package.json`, `pnpm-workspace.yaml`
- `.eslintrc.js`, `.prettierrc.js`, `.husky/pre-commit`
- `README.md`, `LICENSE`, `.nvmrc`

---

### TASK-002: Backend API Project Setup
**ID**: TASK-002
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-001
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Backend developer

**Description**: Initialize Express + TypeScript backend with Prisma ORM, configure environment variables, and create basic server structure.

**Subtasks**:
- [ ] Initialize TypeScript project in `/api` with `tsconfig.json`
- [ ] Install dependencies: express, prisma, zod, bcrypt, jsonwebtoken, cors, helmet, express-rate-limit
- [ ] Install dev dependencies: @types/node, @types/express, tsx, vitest
- [ ] Create Express server entry point (`src/server.ts`)
- [ ] Configure environment variables with `.env.example` template
- [ ] Set up Prisma with PostgreSQL datasource
- [ ] Create basic folder structure: `/src/routes`, `/src/controllers`, `/src/middleware`, `/src/services`
- [ ] Implement `/health` endpoint for uptime monitoring
- [ ] Add scripts to `package.json`: `dev`, `build`, `start`, `test`

**Acceptance Criteria**:
- [ ] Server starts successfully with `pnpm dev` on port 3000
- [ ] `GET /health` returns 200 OK with JSON response
- [ ] Hot reload works when modifying TypeScript files
- [ ] TypeScript compilation produces no errors
- [ ] Prisma client generates successfully

**Technical Notes**:
- Use `tsx` for development (faster than ts-node)
- Configure `tsconfig.json` with `strict: true` for maximum type safety
- Environment variables validated at startup with Zod schema

**Files to Create**:
- `api/package.json`, `api/tsconfig.json`, `api/.env.example`
- `api/src/server.ts`, `api/src/config/env.ts`
- `api/prisma/schema.prisma`

---

### TASK-003: Database Schema Implementation
**ID**: TASK-003
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-002
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Backend developer

**Description**: Define Prisma database schema for users, tasks, lists, tags, and relationships. Create initial migration and seed data.

**Subtasks**:
- [ ] Define `User` model with email, password_hash, timestamps
- [ ] Define `Task` model with all required fields (title, description, status, priority, due_date, etc.)
- [ ] Define `List` model for task organization
- [ ] Define `Tag` and `TaskTag` junction table for many-to-many relationship
- [ ] Add enums for `Status` (NOT_STARTED, IN_PROGRESS, COMPLETED, BLOCKED)
- [ ] Add enums for `Priority` (LOW, MEDIUM, HIGH, URGENT)
- [ ] Create composite indexes: `[user_id, status]`, `[user_id, due_date]`, `[user_id, list_id]`
- [ ] Add unique constraints: `User.email`, `List[user_id, name]`
- [ ] Run initial migration: `prisma migrate dev --name init`
- [ ] Create seed script (`prisma/seed.ts`) with sample data

**Acceptance Criteria**:
- [ ] `prisma migrate dev` runs without errors
- [ ] All models defined according to architecture document
- [ ] Indexes created for query optimization
- [ ] Seed script creates 1 test user and 10 sample tasks
- [ ] Prisma Studio opens and displays all tables correctly
- [ ] Foreign key relationships properly configured with cascade/set null

**Technical Notes**:
- Use UUIDs for all primary keys (`@default(uuid())`)
- Map Prisma field names to snake_case in database (`@map`)
- Use `@updatedAt` for automatic timestamp updates
- Cascade delete for user → tasks, set null for list → tasks

**Files to Create**:
- `api/prisma/schema.prisma`
- `api/prisma/seed.ts`
- `api/prisma/migrations/YYYYMMDDHHMMSS_init/migration.sql`

---

### TASK-004: Frontend Project Setup
**ID**: TASK-004
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-001
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Initialize React + TypeScript frontend with Vite, configure TailwindCSS, and set up routing and state management.

**Subtasks**:
- [ ] Create Vite + React + TypeScript project in `/frontend`
- [ ] Install dependencies: react, react-dom, react-router-dom, zustand, @tanstack/react-query, axios, zod
- [ ] Install dev dependencies: @types/react, tailwindcss, postcss, autoprefixer, vitest, @testing-library/react
- [ ] Configure TailwindCSS with custom color palette
- [ ] Set up React Router with basic route structure
- [ ] Configure Zustand store for auth state
- [ ] Create Axios instance with base URL and interceptors
- [ ] Set up React Query provider with dev tools
- [ ] Create basic app layout component
- [ ] Add scripts: `dev`, `build`, `preview`, `test`

**Acceptance Criteria**:
- [ ] App runs on `http://localhost:5173` with `pnpm dev`
- [ ] TailwindCSS styles apply correctly (test with utility classes)
- [ ] React Router navigation works between placeholder pages
- [ ] React Query DevTools accessible in development mode
- [ ] TypeScript compilation produces no errors
- [ ] Hot module replacement (HMR) works for React components

**Technical Notes**:
- Use Vite 5 for faster build times
- Configure path aliases in `vite.config.ts` (`@/` → `/src`)
- Set up TailwindCSS with mobile-first breakpoints
- Configure Axios interceptors for auth token injection

**Files to Create**:
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`
- `frontend/tailwind.config.js`, `frontend/postcss.config.js`
- `frontend/src/main.tsx`, `frontend/src/App.tsx`
- `frontend/src/services/api.ts`, `frontend/src/store/authStore.ts`

---

### TASK-005: Development Environment with Docker Compose
**ID**: TASK-005
**Complexity**: M (Medium)
**Effort**: 4 hours
**Dependencies**: TASK-002, TASK-004
**Priority**: High (Developer Experience)
**Assignee Profile**: Backend developer or DevOps-minded developer

**Description**: Create Docker Compose configuration for local development with PostgreSQL, Redis, and hot-reload for API and frontend.

**Subtasks**:
- [ ] Create `docker-compose.dev.yml` with services: postgres, redis, api, frontend
- [ ] Configure PostgreSQL service with volume persistence
- [ ] Configure Redis service (alpine image)
- [ ] Set up API service with volume mounts for hot reload
- [ ] Set up frontend service with Vite dev server
- [ ] Create `.env.docker` with database and Redis URLs
- [ ] Write `Dockerfile.dev` for API with development dependencies
- [ ] Write `Dockerfile.dev` for frontend with Vite
- [ ] Add health checks for postgres and redis
- [ ] Document startup process in README

**Acceptance Criteria**:
- [ ] `docker-compose -f docker-compose.dev.yml up` starts all services successfully
- [ ] API accessible at `http://localhost:3000` from host machine
- [ ] Frontend accessible at `http://localhost:5173` from host machine
- [ ] Database persists data between container restarts
- [ ] Hot reload works for both API and frontend when files change
- [ ] `docker-compose down` cleans up containers properly

**Technical Notes**:
- Use named volumes for database persistence
- Bind mount source code directories for hot reload
- Configure depends_on with health checks to ensure startup order
- Use PostgreSQL 14+ and Redis 7 alpine images

**Files to Create**:
- `docker-compose.dev.yml`
- `api/Dockerfile.dev`, `frontend/Dockerfile.dev`
- `.env.docker`
- `scripts/dev-start.sh` (convenience script)

---

### TASK-006: CI/CD Pipeline Setup
**ID**: TASK-006
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-002, TASK-004
**Priority**: Medium (Can be done in parallel with feature development)
**Assignee Profile**: Developer with CI/CD experience

**Description**: Configure GitHub Actions workflows for automated testing, linting, and deployment to staging environment.

**Subtasks**:
- [ ] Create `.github/workflows/test.yml` for running tests on PR
- [ ] Add lint job to workflow (ESLint + Prettier check)
- [ ] Add unit test job for backend (Vitest)
- [ ] Add unit test job for frontend (Vitest + React Testing Library)
- [ ] Configure test coverage reporting
- [ ] Create `.github/workflows/deploy-staging.yml` for staging deployment
- [ ] Set up deployment to Railway.app or DigitalOcean App Platform
- [ ] Configure environment secrets in GitHub repository settings
- [ ] Add status badge to README
- [ ] Test workflow by creating a test PR

**Acceptance Criteria**:
- [ ] Test workflow runs on every PR and main branch push
- [ ] Workflow fails if linting errors or test failures occur
- [ ] Coverage report posted as comment on PR (optional)
- [ ] Deployment workflow triggers on push to `develop` branch
- [ ] Staging environment updates automatically after successful deployment
- [ ] Status badge displays current build status in README

**Technical Notes**:
- Use GitHub Actions cache for faster pnpm installs
- Run frontend and backend tests in parallel jobs
- Set Node.js version to 20.x in workflow
- Use secrets for deployment tokens and database URLs

**Files to Create**:
- `.github/workflows/test.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/lighthouse.yml` (optional performance testing)

---

### TASK-007: Shared TypeScript Types Package
**ID**: TASK-007
**Complexity**: S (Small)
**Effort**: 3 hours
**Dependencies**: TASK-003
**Priority**: High (Enables type safety across frontend/backend)
**Assignee Profile**: Backend developer

**Description**: Create shared TypeScript types for API contracts, DTOs, and domain models to ensure type safety between frontend and backend.

**Subtasks**:
- [ ] Generate Prisma types: `prisma generate`
- [ ] Create `/api/src/types/api.ts` for request/response types
- [ ] Define `CreateTaskDTO`, `UpdateTaskDTO`, `TaskFilters` interfaces
- [ ] Define `PaginatedResponse<T>` generic type
- [ ] Define `ApiError` interface for error responses
- [ ] Export Prisma-generated types (`Task`, `User`, `List`, `Tag`)
- [ ] Create Zod schemas matching TypeScript types for validation
- [ ] Copy shared types to `/frontend/src/types/` (or use symlink)
- [ ] Configure TypeScript path resolution for shared types

**Acceptance Criteria**:
- [ ] Prisma client types available in backend code
- [ ] DTO interfaces used in API route handlers
- [ ] Frontend can import and use shared types
- [ ] Zod schemas validate runtime data against TypeScript types
- [ ] No type errors when building frontend or backend
- [ ] IntelliSense works for shared types in both projects

**Technical Notes**:
- Use Zod's `.infer<>` to derive TypeScript types from schemas
- Consider using a dedicated `/shared` package in monorepo (optional)
- Export enums for `TaskStatus`, `TaskPriority` from Prisma schema

**Files to Create**:
- `api/src/types/api.ts`
- `api/src/schemas/task.schema.ts`
- `frontend/src/types/api.ts` (copied or symlinked)

---

## Phase 2: Authentication Module

**Duration**: 5 days
**Effort**: 40-48 hours
**Goal**: Implement secure user registration, login, logout with JWT authentication

---

### TASK-008: Authentication Service (Backend)
**ID**: TASK-008
**Complexity**: L (Large)
**Effort**: 8 hours
**Dependencies**: TASK-007
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Senior backend developer

**Description**: Implement authentication service with JWT token generation, password hashing, and user management business logic.

**Subtasks**:
- [ ] Create `/api/src/services/auth.service.ts`
- [ ] Implement `registerUser()`: validate email uniqueness, hash password (bcrypt 12 rounds), create user record
- [ ] Implement `loginUser()`: verify credentials, check account lock status, generate JWT
- [ ] Implement `generateToken()`: create JWT with user_id, email, 24h expiration
- [ ] Implement `verifyToken()`: validate JWT signature and expiration
- [ ] Create password validation function (min 8 chars, uppercase, lowercase, number)
- [ ] Implement account lockout logic: 5 failed attempts → 15 min lock
- [ ] Use Redis for storing failed login attempts counter
- [ ] Add error handling: `UserAlreadyExistsError`, `InvalidCredentialsError`, `AccountLockedError`
- [ ] Write unit tests for all service methods (80% coverage target)

**Acceptance Criteria**:
- [ ] User registration creates new user with hashed password
- [ ] Duplicate email registration returns 400 error
- [ ] Login with valid credentials returns JWT token
- [ ] Login with invalid credentials returns generic error (no email/password hint)
- [ ] Account locks after 5 failed login attempts within 15 minutes
- [ ] JWT token contains correct payload (user_id, email, exp)
- [ ] Token verification correctly identifies expired/invalid tokens
- [ ] All unit tests pass with 80%+ coverage

**Technical Notes**:
- Use bcrypt with 12 salt rounds (~250ms computation)
- JWT secret loaded from environment variable
- Store failed attempts in Redis with 15-min TTL
- Use UUIDs for JWT ID (jti) for future revocation support

**Files to Create**:
- `api/src/services/auth.service.ts`
- `api/src/utils/jwt.ts`
- `api/src/utils/password.ts`
- `api/src/__tests__/services/auth.service.test.ts`

---

### TASK-009: Authentication Middleware (Backend)
**ID**: TASK-009
**Complexity**: M (Medium)
**Effort**: 4 hours
**Dependencies**: TASK-008
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Backend developer

**Description**: Create Express middleware for JWT authentication, authorization, and rate limiting on auth endpoints.

**Subtasks**:
- [ ] Create `/api/src/middleware/auth.middleware.ts`
- [ ] Implement `authenticateToken()`: extract JWT from Authorization header, verify token, attach user to `req.user`
- [ ] Implement `requireAuth()`: return 401 if not authenticated
- [ ] Create rate limiting middleware using `express-rate-limit` + Redis store
- [ ] Configure auth endpoint rate limit: 5 requests per 15 min per IP
- [ ] Configure global API rate limit: 100 requests per min per user
- [ ] Add CORS middleware with whitelist for allowed origins
- [ ] Add helmet middleware for security headers
- [ ] Write middleware unit tests

**Acceptance Criteria**:
- [ ] Protected routes return 401 Unauthorized if no token provided
- [ ] Protected routes return 401 if token is expired or invalid
- [ ] Valid token allows access to protected routes
- [ ] `req.user` contains user ID and email after authentication
- [ ] Rate limiting blocks requests after threshold exceeded
- [ ] Rate limit headers included in response (X-RateLimit-*)
- [ ] CORS allows requests only from whitelisted origins
- [ ] Helmet sets security headers (CSP, HSTS, etc.)

**Technical Notes**:
- Token format: `Authorization: Bearer <jwt_token>`
- Use Redis for distributed rate limiting (supports multiple API instances)
- Configure CORS to allow `http://localhost:5173` in development
- Set `httpOnly`, `secure`, `sameSite` for cookies if using cookie-based auth

**Files to Create**:
- `api/src/middleware/auth.middleware.ts`
- `api/src/middleware/rateLimit.middleware.ts`
- `api/src/middleware/cors.middleware.ts`
- `api/src/__tests__/middleware/auth.middleware.test.ts`

---

### TASK-010: Authentication Routes & Controllers (Backend)
**ID**: TASK-010
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-009
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Backend developer

**Description**: Create RESTful API endpoints for user registration, login, logout, and current user retrieval.

**Subtasks**:
- [ ] Create `/api/src/controllers/auth.controller.ts`
- [ ] Implement `register()`: validate input with Zod, call auth service, return user + token
- [ ] Implement `login()`: validate credentials, return user + token
- [ ] Implement `logout()`: invalidate token (optional - client-side for stateless JWT)
- [ ] Implement `getCurrentUser()`: return current user data from `req.user`
- [ ] Create `/api/src/routes/auth.routes.ts`
- [ ] Define routes: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
- [ ] Apply validation middleware with Zod schemas
- [ ] Apply rate limiting to register and login endpoints
- [ ] Mount auth routes in main server
- [ ] Write integration tests with Supertest

**Acceptance Criteria**:
- [ ] `POST /api/v1/auth/register` creates user and returns 201 with token
- [ ] `POST /api/v1/auth/login` authenticates user and returns 200 with token
- [ ] `GET /api/v1/auth/me` returns current user data (requires auth)
- [ ] Invalid input returns 400 with validation errors
- [ ] Duplicate email returns 400 error
- [ ] Invalid credentials return 401 error
- [ ] Rate limiting enforced (429 status after threshold)
- [ ] All integration tests pass

**Technical Notes**:
- Use Zod for request body validation
- Return consistent error format across all endpoints
- Log failed login attempts for security monitoring
- Consider implementing refresh token endpoint (post-MVP)

**Files to Create**:
- `api/src/controllers/auth.controller.ts`
- `api/src/routes/auth.routes.ts`
- `api/src/schemas/auth.schema.ts`
- `api/src/__tests__/routes/auth.routes.test.ts`

---

### TASK-011: Authentication UI Components (Frontend)
**ID**: TASK-011
**Complexity**: L (Large)
**Effort**: 8 hours
**Dependencies**: TASK-010 (API contract defined)
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer
**Can Run in Parallel**: Yes (after API contract is defined)

**Description**: Create React components for login and registration forms with validation, error handling, and loading states.

**Subtasks**:
- [ ] Create `/frontend/src/components/auth/LoginForm.tsx`
- [ ] Create `/frontend/src/components/auth/RegisterForm.tsx`
- [ ] Use React Hook Form for form state management
- [ ] Implement client-side validation with Zod schemas (matching backend)
- [ ] Style forms with TailwindCSS (centered card layout, responsive)
- [ ] Add loading spinners during API requests
- [ ] Display error messages from API responses
- [ ] Implement password visibility toggle
- [ ] Add "Remember me" checkbox (optional - extends JWT expiration)
- [ ] Create success states (redirect to dashboard after login/register)
- [ ] Add form accessibility (labels, ARIA attributes, keyboard navigation)
- [ ] Write component tests with React Testing Library

**Acceptance Criteria**:
- [ ] Login form validates email format and required fields
- [ ] Registration form enforces password requirements
- [ ] Forms display loading state during API calls
- [ ] API errors displayed to user in user-friendly format
- [ ] Successful login/registration redirects to dashboard
- [ ] Password toggle shows/hides password text
- [ ] Forms are keyboard accessible (Tab, Enter navigation)
- [ ] WCAG AA contrast ratios met for text and inputs
- [ ] Component tests cover success and error scenarios

**Technical Notes**:
- Use React Hook Form with Zod resolver for validation
- Store JWT token in Zustand auth store or localStorage
- Use Axios interceptors to include token in subsequent requests
- Consider social login UI (Google, GitHub) for post-MVP

**Files to Create**:
- `frontend/src/components/auth/LoginForm.tsx`
- `frontend/src/components/auth/RegisterForm.tsx`
- `frontend/src/components/shared/Input.tsx`
- `frontend/src/components/shared/Button.tsx`
- `frontend/src/__tests__/components/auth/LoginForm.test.tsx`

---

### TASK-012: Auth State Management & Protected Routes (Frontend)
**ID**: TASK-012
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-011
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Implement Zustand store for authentication state and create protected route wrapper for authenticated pages.

**Subtasks**:
- [ ] Enhance `/frontend/src/store/authStore.ts` with login, logout, register actions
- [ ] Implement `login()`: call API, store token, update user state
- [ ] Implement `register()`: call API, store token, update user state
- [ ] Implement `logout()`: clear token, reset user state
- [ ] Implement `checkAuth()`: verify token validity on app load
- [ ] Create `/frontend/src/components/auth/ProtectedRoute.tsx`
- [ ] Redirect unauthenticated users to login page
- [ ] Persist auth state to localStorage for session continuity
- [ ] Configure Axios interceptor to include Authorization header
- [ ] Handle 401 responses globally (auto-logout on token expiration)
- [ ] Write tests for auth store actions

**Acceptance Criteria**:
- [ ] Login action stores JWT token and user data in Zustand store
- [ ] Logout action clears all auth state
- [ ] Auth state persists across browser refreshes (localStorage)
- [ ] ProtectedRoute redirects to `/login` if user not authenticated
- [ ] Axios includes `Authorization: Bearer <token>` header on all API requests
- [ ] 401 responses trigger automatic logout and redirect to login
- [ ] Auth state updates trigger re-render of dependent components
- [ ] Store tests verify correct state updates

**Technical Notes**:
- Use Zustand persist middleware for localStorage sync
- Validate token expiration client-side before API calls (optional optimization)
- Consider implementing token refresh logic (post-MVP)
- Use React Router's `Navigate` component for redirects

**Files to Create**:
- `frontend/src/store/authStore.ts` (enhanced)
- `frontend/src/components/auth/ProtectedRoute.tsx`
- `frontend/src/services/authService.ts`
- `frontend/src/__tests__/store/authStore.test.ts`

---

### TASK-013: Auth Pages & Routing (Frontend)
**ID**: TASK-013
**Complexity**: S (Small)
**Effort**: 4 hours
**Dependencies**: TASK-012
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Create login and registration pages with routing, integrate auth forms, and implement post-auth redirects.

**Subtasks**:
- [ ] Create `/frontend/src/pages/LoginPage.tsx`
- [ ] Create `/frontend/src/pages/RegisterPage.tsx`
- [ ] Create `/frontend/src/pages/DashboardPage.tsx` (placeholder for now)
- [ ] Configure React Router routes in App.tsx
- [ ] Add route: `/login` → LoginPage
- [ ] Add route: `/register` → RegisterPage
- [ ] Add route: `/dashboard` → ProtectedRoute(DashboardPage)
- [ ] Implement redirect logic: authenticated users accessing `/login` → `/dashboard`
- [ ] Add navigation links between login and register pages
- [ ] Style pages with centered card layout, responsive design
- [ ] Test navigation flows

**Acceptance Criteria**:
- [ ] `/login` displays login form for unauthenticated users
- [ ] `/register` displays registration form
- [ ] Successful login redirects to `/dashboard`
- [ ] Successful registration redirects to `/dashboard`
- [ ] `/dashboard` redirects to `/login` if user not authenticated
- [ ] Authenticated users accessing `/login` redirected to `/dashboard`
- [ ] Navigation links work correctly between pages
- [ ] Pages are responsive on mobile, tablet, desktop

**Technical Notes**:
- Use React Router 6 with declarative routing
- Implement route guards in ProtectedRoute component
- Consider adding a "Forgot Password" link (post-MVP feature)
- Add page titles for SEO and accessibility

**Files to Create**:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/App.tsx` (updated with routes)

---

### TASK-014: Authentication Integration Testing
**ID**: TASK-014
**Complexity**: M (Medium)
**Effort**: 4 hours
**Dependencies**: TASK-013
**Priority**: High (Quality Gate)
**Assignee Profile**: Backend or frontend developer

**Description**: Write end-to-end integration tests for complete authentication flows using Playwright or Cypress.

**Subtasks**:
- [ ] Set up Playwright test environment
- [ ] Write test: "User can register new account"
- [ ] Write test: "User can login with valid credentials"
- [ ] Write test: "Login fails with invalid credentials"
- [ ] Write test: "Duplicate email registration returns error"
- [ ] Write test: "Protected routes redirect unauthenticated users"
- [ ] Write test: "User can logout successfully"
- [ ] Write test: "Session persists after browser refresh"
- [ ] Configure test database seeding for consistent test data
- [ ] Add E2E tests to CI/CD pipeline

**Acceptance Criteria**:
- [ ] All E2E tests pass locally
- [ ] Tests run in CI/CD pipeline on every PR
- [ ] Tests cover happy path and error scenarios
- [ ] Test suite completes in <2 minutes
- [ ] Tests are deterministic (no flakiness)
- [ ] Test database isolated from development database

**Technical Notes**:
- Use Playwright for cross-browser testing
- Run tests against Docker Compose environment
- Seed test database before each test run
- Clean up test data after tests complete

**Files to Create**:
- `e2e/tests/auth.spec.ts`
- `e2e/playwright.config.ts`
- `scripts/seed-test-db.ts`

---

## Phase 3: Core Task CRUD

**Duration**: 7 days
**Effort**: 56-72 hours
**Goal**: Implement complete task creation, reading, updating, and deletion functionality

---

### TASK-015: Task Service & Repository (Backend)
**ID**: TASK-015
**Complexity**: L (Large)
**Effort**: 8 hours
**Dependencies**: TASK-007
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Backend developer

**Description**: Implement task management service with CRUD operations, pagination, and business logic for task lifecycle.

**Subtasks**:
- [ ] Create `/api/src/services/task.service.ts`
- [ ] Implement `createTask()`: validate input, set defaults (status=NOT_STARTED, priority=MEDIUM), create task record
- [ ] Implement `getTasks()`: fetch user's tasks with pagination, filtering, sorting
- [ ] Implement `getTaskById()`: fetch single task, verify ownership
- [ ] Implement `updateTask()`: validate input, update task, handle completed_at timestamp
- [ ] Implement `deleteTask()`: verify ownership, hard delete task
- [ ] Implement `updateTaskStatus()`: quick status change, set completed_at if status=COMPLETED
- [ ] Implement pagination helper: calculate offset, limit, total pages
- [ ] Add query optimization: select only needed fields, eager load relations
- [ ] Write unit tests for all service methods (80% coverage)

**Acceptance Criteria**:
- [ ] Tasks are always filtered by user_id (no cross-user data leaks)
- [ ] Pagination returns correct page, total count, has_next/has_prev flags
- [ ] Status change to COMPLETED sets completed_at timestamp
- [ ] Reopening completed task clears completed_at
- [ ] Default values applied (status, priority) when not provided
- [ ] Service throws errors for unauthorized access attempts
- [ ] All unit tests pass with 80%+ coverage
- [ ] Query performance <100ms for 10,000 tasks (verified with EXPLAIN)

**Technical Notes**:
- Use Prisma's `findMany` with `where`, `orderBy`, `skip`, `take`
- Implement cursor-based pagination for better performance (optional)
- Use transactions for operations affecting multiple tables
- Log task creation/updates for audit trail (optional)

**Files to Create**:
- `api/src/services/task.service.ts`
- `api/src/utils/pagination.ts`
- `api/src/__tests__/services/task.service.test.ts`

---

### TASK-016: Task Routes & Controllers (Backend)
**ID**: TASK-016
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-015
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Backend developer

**Description**: Create RESTful API endpoints for task CRUD operations with validation, authorization, and error handling.

**Subtasks**:
- [ ] Create `/api/src/controllers/task.controller.ts`
- [ ] Implement `createTask()`: validate input, call service, return 201
- [ ] Implement `getTasks()`: parse query params, call service, return paginated response
- [ ] Implement `getTaskById()`: validate UUID, call service, return 200
- [ ] Implement `updateTask()`: validate input, verify ownership, call service
- [ ] Implement `deleteTask()`: verify ownership, call service, return 204
- [ ] Implement `updateTaskStatus()`: quick status update endpoint
- [ ] Create `/api/src/routes/task.routes.ts`
- [ ] Define routes: `GET /tasks`, `POST /tasks`, `GET /tasks/:id`, `PUT /tasks/:id`, `DELETE /tasks/:id`, `PATCH /tasks/:id/status`
- [ ] Apply auth middleware to all routes
- [ ] Apply validation middleware with Zod schemas
- [ ] Write integration tests with Supertest

**Acceptance Criteria**:
- [ ] `POST /api/v1/tasks` creates task and returns 201 with task data
- [ ] `GET /api/v1/tasks` returns paginated task list
- [ ] `GET /api/v1/tasks/:id` returns single task or 404
- [ ] `PUT /api/v1/tasks/:id` updates task and returns 200
- [ ] `DELETE /api/v1/tasks/:id` deletes task and returns 204
- [ ] `PATCH /api/v1/tasks/:id/status` updates status only
- [ ] 403 error returned when user tries to access another user's task
- [ ] 400 error returned for validation failures
- [ ] All integration tests pass

**Technical Notes**:
- Use `:id` route parameter for task ID
- Validate UUIDs before database queries
- Return consistent error response format
- Include pagination metadata in GET /tasks response

**Files to Create**:
- `api/src/controllers/task.controller.ts`
- `api/src/routes/task.routes.ts`
- `api/src/schemas/task.schema.ts`
- `api/src/__tests__/routes/task.routes.test.ts`

---

### TASK-017: Task API Client & React Query Hooks (Frontend)
**ID**: TASK-017
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-016 (API contract defined)
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer
**Can Run in Parallel**: Yes (after API contract is defined)

**Description**: Create React Query hooks for task CRUD operations with optimistic updates, caching, and error handling.

**Subtasks**:
- [ ] Create `/frontend/src/services/taskService.ts` with API client methods
- [ ] Implement `getTasks()`: fetch tasks with query params (filters, pagination)
- [ ] Implement `getTaskById()`: fetch single task
- [ ] Implement `createTask()`: POST new task
- [ ] Implement `updateTask()`: PUT task updates
- [ ] Implement `deleteTask()`: DELETE task
- [ ] Create `/frontend/src/hooks/useTasks.ts` with React Query hooks
- [ ] Implement `useTasks()`: query hook with caching, pagination
- [ ] Implement `useTask(id)`: query hook for single task
- [ ] Implement `useCreateTask()`: mutation hook with optimistic update
- [ ] Implement `useUpdateTask()`: mutation hook with optimistic update
- [ ] Implement `useDeleteTask()`: mutation hook with optimistic update
- [ ] Configure cache invalidation strategy

**Acceptance Criteria**:
- [ ] `useTasks()` fetches and caches task list
- [ ] Cache automatically refetches when user returns to tab (staleTime)
- [ ] Create/update/delete mutations trigger cache invalidation
- [ ] Optimistic updates show changes immediately before server response
- [ ] Rollback on error (revert optimistic update)
- [ ] Loading and error states available in components
- [ ] React Query DevTools show cached queries
- [ ] All hooks have proper TypeScript types

**Technical Notes**:
- Use React Query 5 with `useQuery`, `useMutation`
- Configure `staleTime: 5 minutes`, `cacheTime: 30 minutes`
- Use `queryClient.invalidateQueries()` for cache invalidation
- Implement optimistic updates with `onMutate`, `onError`, `onSettled`

**Files to Create**:
- `frontend/src/services/taskService.ts`
- `frontend/src/hooks/useTasks.ts`
- `frontend/src/types/task.ts`
- `frontend/src/__tests__/hooks/useTasks.test.ts`

---

### TASK-018: Task List Component (Frontend)
**ID**: TASK-018
**Complexity**: L (Large)
**Effort**: 10 hours
**Dependencies**: TASK-017
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Create task list component with virtualization, sorting, filtering, and inline actions (status change, delete).

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/TaskList.tsx`
- [ ] Fetch tasks using `useTasks()` hook
- [ ] Display tasks in card/row layout with title, status, priority, due date
- [ ] Implement virtualization with `react-window` for 100+ tasks
- [ ] Add loading skeleton while tasks load
- [ ] Add empty state when no tasks ("No tasks yet. Create your first task!")
- [ ] Implement inline status change (dropdown or buttons)
- [ ] Add delete button with confirmation dialog
- [ ] Color-code priority: Urgent=red, High=orange, Medium=yellow, Low=gray
- [ ] Show overdue indicator (red flag) when due_date < today and status != COMPLETED
- [ ] Make task rows clickable to open detail modal
- [ ] Implement pagination controls (Previous/Next buttons)
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Task list displays all user's tasks from API
- [ ] Tasks sorted by created_at desc by default
- [ ] Priority color-coding visually distinct
- [ ] Overdue tasks show red indicator
- [ ] Status change updates immediately (optimistic update)
- [ ] Delete confirmation prevents accidental deletion
- [ ] Loading state shown during initial fetch
- [ ] Empty state shown when user has no tasks
- [ ] Pagination works correctly (page numbers, navigation)
- [ ] Component tests cover rendering and interactions

**Technical Notes**:
- Use `react-window` or `react-virtualized` for performance with large lists
- Implement debounce for search input (300ms)
- Use React.memo to prevent unnecessary re-renders
- Consider table view and kanban board view (post-MVP)

**Files to Create**:
- `frontend/src/components/tasks/TaskList.tsx`
- `frontend/src/components/tasks/TaskCard.tsx`
- `frontend/src/components/shared/EmptyState.tsx`
- `frontend/src/__tests__/components/tasks/TaskList.test.tsx`

---

### TASK-019: Task Creation Form (Frontend)
**ID**: TASK-019
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-017
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Create task creation modal/form with all fields, validation, and quick-add option for title-only tasks.

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/TaskCreateModal.tsx`
- [ ] Use React Hook Form for form state management
- [ ] Add form fields: title (required), description, priority, status, due_date, list, tags
- [ ] Implement Zod validation matching backend schema
- [ ] Add date picker component for due_date field
- [ ] Add tag input with autocomplete (comma-separated or tag chips)
- [ ] Create quick-add input: inline text input for title-only task creation
- [ ] Show full form when "More details" clicked
- [ ] Call `useCreateTask()` mutation on submit
- [ ] Show loading spinner during creation
- [ ] Display success notification and close modal on success
- [ ] Display error message on failure
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Modal opens when "New Task" button clicked
- [ ] Quick-add creates task with only title (default priority, status)
- [ ] Full form allows setting all task fields
- [ ] Client-side validation prevents invalid submissions
- [ ] Date picker allows selecting due dates
- [ ] Tag autocomplete suggests existing tags
- [ ] Task appears in list immediately after creation (optimistic update)
- [ ] Error messages displayed for API failures
- [ ] Form resets after successful creation
- [ ] Keyboard accessible (Tab, Enter, Escape)

**Technical Notes**:
- Use headlessUI Modal component or Radix UI Dialog
- Use react-day-picker for date selection
- Store modal open state in UI store (Zustand)
- Consider hotkey "N" to open create modal (post-MVP)

**Files to Create**:
- `frontend/src/components/tasks/TaskCreateModal.tsx`
- `frontend/src/components/tasks/QuickAddTask.tsx`
- `frontend/src/components/shared/Modal.tsx`
- `frontend/src/components/shared/DatePicker.tsx`
- `frontend/src/__tests__/components/tasks/TaskCreateModal.test.tsx`

---

### TASK-020: Task Detail & Edit Modal (Frontend)
**ID**: TASK-020
**Complexity**: L (Large)
**Effort**: 8 hours
**Dependencies**: TASK-017
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Create task detail modal with inline editing, full CRUD operations, and rich metadata display.

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/TaskDetailModal.tsx`
- [ ] Display task in read-only mode initially
- [ ] Show all fields: title, description, status, priority, due_date, list, tags, created_at, updated_at
- [ ] Add "Edit" button to switch to edit mode
- [ ] In edit mode, use same form fields as create modal
- [ ] Call `useUpdateTask()` mutation on save
- [ ] Add "Delete" button with confirmation dialog
- [ ] Call `useDeleteTask()` mutation on delete
- [ ] Show timestamps: "Created 2 days ago", "Updated 1 hour ago"
- [ ] Display completion timestamp if status=COMPLETED
- [ ] Add "Mark as Complete" quick action button
- [ ] Implement keyboard shortcuts: Escape to close, E to edit
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Modal opens when task card clicked
- [ ] All task details displayed correctly
- [ ] Edit mode allows modifying all fields
- [ ] Save updates task and shows changes immediately
- [ ] Delete removes task from list after confirmation
- [ ] Completion timestamp shown for completed tasks
- [ ] Quick action buttons work (mark complete, delete)
- [ ] Keyboard shortcuts functional
- [ ] Optimistic updates work correctly
- [ ] Error handling displays user-friendly messages

**Technical Notes**:
- Use same Modal component as task creation
- Toggle between read and edit mode with state
- Use React Hook Form for edit mode
- Consider rich text editor for description (post-MVP)

**Files to Create**:
- `frontend/src/components/tasks/TaskDetailModal.tsx`
- `frontend/src/components/tasks/TaskEditForm.tsx`
- `frontend/src/__tests__/components/tasks/TaskDetailModal.test.tsx`

---

### TASK-021: Dashboard Page Layout (Frontend)
**ID**: TASK-021
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-018, TASK-019
**Priority**: Critical (MVP Blocker)
**Assignee Profile**: Frontend developer

**Description**: Create main dashboard layout with sidebar navigation, header, and task list integration.

**Subtasks**:
- [ ] Create `/frontend/src/components/layout/MainLayout.tsx`
- [ ] Create `/frontend/src/components/layout/Sidebar.tsx`
- [ ] Create `/frontend/src/components/layout/Header.tsx`
- [ ] Implement responsive layout: sidebar visible on desktop, hamburger menu on mobile
- [ ] Add sidebar navigation: "All Tasks", "Today", "Upcoming", "Completed"
- [ ] Add header with user menu (logout option)
- [ ] Add "New Task" button in header
- [ ] Integrate TaskList component in main content area
- [ ] Apply TailwindCSS for responsive grid layout
- [ ] Test on desktop (1920px), tablet (768px), mobile (375px)
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Sidebar shows navigation links on desktop (>1024px)
- [ ] Hamburger menu shows sidebar overlay on mobile (<768px)
- [ ] Header contains app title, new task button, user menu
- [ ] User menu allows logout
- [ ] Task list occupies main content area
- [ ] Layout responsive across all breakpoints
- [ ] Sidebar navigation changes active task filter
- [ ] All navigation functional
- [ ] Components render without errors

**Technical Notes**:
- Use CSS Grid for main layout (sidebar + content)
- Use headlessUI Menu for user dropdown
- Store sidebar open/closed state in UI store
- Consider adding breadcrumbs for navigation context

**Files to Create**:
- `frontend/src/components/layout/MainLayout.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/pages/DashboardPage.tsx` (updated)

---

### TASK-022: Task CRUD Integration Testing
**ID**: TASK-022
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-021
**Priority**: High (Quality Gate)
**Assignee Profile**: Frontend or backend developer

**Description**: Write end-to-end tests for complete task management workflows including creation, editing, and deletion.

**Subtasks**:
- [ ] Write E2E test: "User can create a new task"
- [ ] Write E2E test: "User can view task details"
- [ ] Write E2E test: "User can edit task fields"
- [ ] Write E2E test: "User can change task status"
- [ ] Write E2E test: "User can delete task"
- [ ] Write E2E test: "User can create quick task with title only"
- [ ] Write E2E test: "Pagination works correctly"
- [ ] Write E2E test: "Empty state shows when no tasks"
- [ ] Add tests to CI/CD pipeline
- [ ] Verify tests pass on multiple browsers

**Acceptance Criteria**:
- [ ] All E2E tests pass locally and in CI
- [ ] Tests cover happy path and edge cases
- [ ] Test suite completes in <3 minutes
- [ ] Tests are deterministic (no flakiness)
- [ ] Screenshots captured on failure for debugging

**Technical Notes**:
- Use Playwright for cross-browser testing
- Seed database with test data before tests
- Clean up test data after tests complete
- Use Page Object Model pattern for maintainability

**Files to Create**:
- `e2e/tests/tasks.spec.ts`
- `e2e/pages/DashboardPage.ts` (Page Object)
- `e2e/pages/TaskDetailModal.ts` (Page Object)

---

## Phase 4: Task Organization Features

**Duration**: 8 days
**Effort**: 64-80 hours
**Goal**: Implement lists/projects, tags, priorities, and due dates for task organization

---

### TASK-023: List/Project Service & Routes (Backend)
**ID**: TASK-023
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-015
**Priority**: High (MVP Critical)
**Assignee Profile**: Backend developer

**Description**: Implement list/project management service and API endpoints for task categorization.

**Subtasks**:
- [ ] Create `/api/src/services/list.service.ts`
- [ ] Implement `createList()`: validate name uniqueness per user, create list
- [ ] Implement `getLists()`: fetch user's lists with task counts
- [ ] Implement `updateList()`: rename list, change color
- [ ] Implement `deleteList()`: handle task reassignment (move to uncategorized or delete)
- [ ] Enforce max 50 lists per user
- [ ] Create `/api/src/controllers/list.controller.ts`
- [ ] Create `/api/src/routes/list.routes.ts`
- [ ] Define routes: `GET /lists`, `POST /lists`, `PUT /lists/:id`, `DELETE /lists/:id`
- [ ] Write unit and integration tests

**Acceptance Criteria**:
- [ ] Lists created successfully with unique names per user
- [ ] Duplicate list names return 400 error
- [ ] GET /lists returns all user lists with task counts
- [ ] List update changes name/color
- [ ] List deletion prompts for task handling decision
- [ ] Max 50 lists enforced
- [ ] All tests pass with 80%+ coverage

**Technical Notes**:
- Use Prisma transaction for list deletion + task reassignment
- Default "Uncategorized" list created for new users (in seed script)
- Color stored as hex code (#3b82f6)

**Files to Create**:
- `api/src/services/list.service.ts`
- `api/src/controllers/list.controller.ts`
- `api/src/routes/list.routes.ts`
- `api/src/schemas/list.schema.ts`
- `api/src/__tests__/services/list.service.test.ts`

---

### TASK-024: Tag Service & Routes (Backend)
**ID**: TASK-024
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-015
**Priority**: Medium (MVP Nice-to-Have)
**Assignee Profile**: Backend developer

**Description**: Implement tag management service with autocomplete, many-to-many relationships, and usage tracking.

**Subtasks**:
- [ ] Create `/api/src/services/tag.service.ts`
- [ ] Implement `getTags()`: fetch all user tags with usage counts
- [ ] Implement `getTagAutocomplete()`: search tags by name prefix
- [ ] Implement `addTagsToTask()`: create tags if not exist, link to task
- [ ] Implement `removeTagsFromTask()`: unlink tags, delete unused tags
- [ ] Implement case-insensitive tag matching
- [ ] Enforce max 10 tags per task
- [ ] Create `/api/src/controllers/tag.controller.ts`
- [ ] Create `/api/src/routes/tag.routes.ts`
- [ ] Define routes: `GET /tags`, `GET /tags/autocomplete`, `POST /tasks/:id/tags`, `DELETE /tasks/:id/tags`
- [ ] Write unit and integration tests

**Acceptance Criteria**:
- [ ] Tags created on first use, reused on subsequent tagging
- [ ] Autocomplete returns matching tags (case-insensitive)
- [ ] Tags removed from task when last usage deleted
- [ ] Max 10 tags per task enforced
- [ ] Tag usage counts accurate
- [ ] All tests pass with 80%+ coverage

**Technical Notes**:
- Store tags globally (not per-user) for autocomplete suggestions
- Use Prisma transaction for tag creation + task-tag linking
- Implement tag cleanup job to remove orphaned tags (post-MVP)

**Files to Create**:
- `api/src/services/tag.service.ts`
- `api/src/controllers/tag.controller.ts`
- `api/src/routes/tag.routes.ts`
- `api/src/schemas/tag.schema.ts`
- `api/src/__tests__/services/tag.service.test.ts`

---

### TASK-025: List Management UI (Frontend)
**ID**: TASK-025
**Complexity**: M (Medium)
**Effort**: 7 hours
**Dependencies**: TASK-023 (API contract defined)
**Priority**: High (MVP Critical)
**Assignee Profile**: Frontend developer
**Can Run in Parallel**: Yes (after API contract is defined)

**Description**: Create list/project sidebar with CRUD operations, task counts, and drag-and-drop task assignment (optional).

**Subtasks**:
- [ ] Create `/frontend/src/components/lists/ListSidebar.tsx`
- [ ] Fetch lists using React Query hook
- [ ] Display lists in sidebar with name, color, task count
- [ ] Add "New List" button and creation modal
- [ ] Implement list creation with name and color picker
- [ ] Add inline rename functionality (double-click or edit icon)
- [ ] Add delete button with confirmation dialog
- [ ] Show delete options modal: "Move tasks to Uncategorized" or "Delete tasks"
- [ ] Highlight active list
- [ ] Update task list when list selected
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Lists displayed in sidebar with accurate task counts
- [ ] New list creation works with name and color
- [ ] List rename updates immediately (optimistic update)
- [ ] List deletion shows confirmation with task handling options
- [ ] Clicking list filters tasks to that list
- [ ] Active list highlighted visually
- [ ] Color-coded list indicators visible
- [ ] Component tests cover CRUD operations

**Technical Notes**:
- Use React Query hooks: `useLists()`, `useCreateList()`, `useUpdateList()`, `useDeleteList()`
- Store active list ID in URL params or UI store
- Use color picker component (react-colorful or similar)
- Consider drag-and-drop task assignment (post-MVP)

**Files to Create**:
- `frontend/src/components/lists/ListSidebar.tsx`
- `frontend/src/components/lists/ListCreateModal.tsx`
- `frontend/src/components/lists/ListDeleteModal.tsx`
- `frontend/src/hooks/useLists.ts`
- `frontend/src/__tests__/components/lists/ListSidebar.test.tsx`

---

### TASK-026: Tag Input Component (Frontend)
**ID**: TASK-026
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-024 (API contract defined)
**Priority**: Medium (MVP Nice-to-Have)
**Assignee Profile**: Frontend developer
**Can Run in Parallel**: Yes (after API contract is defined)

**Description**: Create tag input component with autocomplete, tag chips, and keyboard navigation.

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/TagInput.tsx`
- [ ] Implement tag chip display with remove button
- [ ] Add input field for new tag entry
- [ ] Fetch tag autocomplete suggestions on input change (debounced)
- [ ] Show dropdown with matching tags
- [ ] Allow creating new tags (press Enter or comma)
- [ ] Limit to 10 tags per task
- [ ] Implement keyboard navigation (Arrow keys, Enter, Backspace)
- [ ] Style tags with color-coded badges
- [ ] Integrate with task create/edit forms
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Tags displayed as chips with remove buttons
- [ ] Autocomplete dropdown shows matching tags
- [ ] Enter or comma creates new tag
- [ ] Backspace removes last tag when input empty
- [ ] Max 10 tags enforced with validation message
- [ ] Keyboard navigation works (arrows, enter, escape)
- [ ] Tags validated (alphanumeric, max 30 chars)
- [ ] Component tests cover interactions

**Technical Notes**:
- Debounce autocomplete API calls (300ms)
- Use downshift or react-select for autocomplete behavior
- Store tags as array of strings in form state
- Validate tag format on client and server

**Files to Create**:
- `frontend/src/components/tasks/TagInput.tsx`
- `frontend/src/components/tasks/TagChip.tsx`
- `frontend/src/hooks/useTags.ts`
- `frontend/src/__tests__/components/tasks/TagInput.test.tsx`

---

### TASK-027: Priority & Status Indicators (Frontend)
**ID**: TASK-027
**Complexity**: S (Small)
**Effort**: 4 hours
**Dependencies**: TASK-018
**Priority**: High (MVP Critical)
**Assignee Profile**: Frontend developer

**Description**: Implement visual priority and status indicators with color coding, icons, and quick-change dropdowns.

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/PriorityBadge.tsx`
- [ ] Color-code priorities: Urgent=red, High=orange, Medium=yellow, Low=gray
- [ ] Add priority icons (optional: flag, exclamation, etc.)
- [ ] Create `/frontend/src/components/tasks/StatusBadge.tsx`
- [ ] Color-code statuses: Not Started=gray, In Progress=blue, Completed=green, Blocked=red
- [ ] Add status icons (checkmark for completed, clock for in progress)
- [ ] Create quick-change dropdowns for inline editing
- [ ] Integrate badges into TaskCard component
- [ ] Add accessibility labels (ARIA)
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Priority badges color-coded correctly
- [ ] Status badges color-coded correctly
- [ ] Icons visible and semantically correct
- [ ] Quick-change dropdowns work in task list
- [ ] Status change triggers API update (optimistic)
- [ ] Accessibility labels present for screen readers
- [ ] Component tests verify rendering for all states

**Technical Notes**:
- Use TailwindCSS badge classes
- Consider using Heroicons or Lucide icons
- Implement dropdown with headlessUI Menu
- Ensure WCAG AA contrast ratios

**Files to Create**:
- `frontend/src/components/tasks/PriorityBadge.tsx`
- `frontend/src/components/tasks/StatusBadge.tsx`
- `frontend/src/components/tasks/PriorityDropdown.tsx`
- `frontend/src/__tests__/components/tasks/PriorityBadge.test.tsx`

---

### TASK-028: Due Date Picker & Overdue Indicators (Frontend)
**ID**: TASK-028
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-019
**Priority**: Medium (MVP Nice-to-Have)
**Assignee Profile**: Frontend developer

**Description**: Implement date picker component for due dates with calendar UI, overdue indicators, and date filters.

**Subtasks**:
- [ ] Enhance DatePicker component with calendar UI
- [ ] Add quick-select options: "Today", "Tomorrow", "Next Week", "Clear"
- [ ] Integrate date picker into task create/edit forms
- [ ] Create `/frontend/src/components/tasks/DueDateBadge.tsx`
- [ ] Show due date with relative formatting ("Due in 2 days", "Due today", "Overdue by 1 day")
- [ ] Add red overdue indicator (icon or badge) when due_date < today and status != COMPLETED
- [ ] Create date filter in sidebar: "Overdue", "Due Today", "Due This Week"
- [ ] Update task list to highlight overdue tasks
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Date picker shows calendar UI with month/year navigation
- [ ] Quick-select options work correctly
- [ ] Due date displayed with relative formatting
- [ ] Overdue tasks show red indicator
- [ ] Date filters in sidebar update task list
- [ ] Overdue tasks visually distinct in list (red border or background)
- [ ] Component tests cover date selection and formatting

**Technical Notes**:
- Use react-day-picker or date-fns for date manipulation
- Store dates in ISO 8601 format (YYYY-MM-DD)
- Calculate overdue status client-side for performance
- Consider timezone handling (use UTC or user's local timezone)

**Files to Create**:
- `frontend/src/components/shared/DatePicker.tsx` (enhanced)
- `frontend/src/components/tasks/DueDateBadge.tsx`
- `frontend/src/utils/dateHelpers.ts`
- `frontend/src/__tests__/components/tasks/DueDateBadge.test.tsx`

---

### TASK-029: Task Filtering UI (Frontend)
**ID**: TASK-029
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-025, TASK-027
**Priority**: High (MVP Critical)
**Assignee Profile**: Frontend developer

**Description**: Create filter UI with multi-select for status, priority, lists, tags, and date ranges with URL state persistence.

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/TaskFilters.tsx`
- [ ] Add filter dropdowns: status (multi-select), priority (multi-select)
- [ ] Add filter for list selection
- [ ] Add filter for tags (multi-select with autocomplete)
- [ ] Add date range filter for due dates
- [ ] Display active filters as removable chips
- [ ] Add "Clear All Filters" button
- [ ] Persist filter state in URL query params
- [ ] Update task list on filter changes
- [ ] Show filter count indicator ("3 filters active")
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] All filter types functional (status, priority, list, tags, date range)
- [ ] Multiple filters combine with AND logic
- [ ] Active filters displayed as chips with remove option
- [ ] Clear all filters resets to default view
- [ ] Filter state persisted in URL (shareable links)
- [ ] Task list updates immediately on filter change
- [ ] Filter count indicator accurate
- [ ] Component tests cover filter combinations

**Technical Notes**:
- Use React Router's `useSearchParams` for URL state
- Debounce filter updates to avoid excessive API calls
- Use multi-select component (headlessUI Listbox or similar)
- Consider saved filter views (post-MVP)

**Files to Create**:
- `frontend/src/components/tasks/TaskFilters.tsx`
- `frontend/src/components/shared/MultiSelect.tsx`
- `frontend/src/hooks/useTaskFilters.ts`
- `frontend/src/__tests__/components/tasks/TaskFilters.test.tsx`

---

### TASK-030: Task Organization Integration Testing
**ID**: TASK-030
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-029
**Priority**: High (Quality Gate)
**Assignee Profile**: Frontend or backend developer

**Description**: Write end-to-end tests for list management, tag assignment, filtering, and task organization workflows.

**Subtasks**:
- [ ] Write E2E test: "User can create and manage lists"
- [ ] Write E2E test: "User can add tags to tasks"
- [ ] Write E2E test: "User can filter tasks by status"
- [ ] Write E2E test: "User can filter tasks by priority"
- [ ] Write E2E test: "User can filter tasks by list"
- [ ] Write E2E test: "User can filter tasks by tags"
- [ ] Write E2E test: "User can combine multiple filters"
- [ ] Write E2E test: "User can see overdue tasks indicator"
- [ ] Add tests to CI/CD pipeline

**Acceptance Criteria**:
- [ ] All E2E tests pass locally and in CI
- [ ] Tests cover CRUD operations for lists and tags
- [ ] Tests verify filter combinations work correctly
- [ ] Tests confirm URL state persistence
- [ ] Test suite completes in <4 minutes

**Technical Notes**:
- Use Playwright for testing
- Seed database with diverse test data (various priorities, statuses, due dates)
- Test filter combinations systematically
- Verify URL updates correctly with filter changes

**Files to Create**:
- `e2e/tests/organization.spec.ts`
- `e2e/pages/FilterPanel.ts` (Page Object)

---

## Phase 5: Search & Filtering

**Duration**: 5 days
**Effort**: 40-48 hours
**Goal**: Implement full-text search, advanced filtering, and sorting capabilities

---

### TASK-031: Full-Text Search Implementation (Backend)
**ID**: TASK-031
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-016
**Priority**: Medium (MVP Nice-to-Have)
**Assignee Profile**: Backend developer

**Description**: Implement PostgreSQL full-text search for task titles and descriptions with ranking and highlighting.

**Subtasks**:
- [ ] Add full-text search indexes to database: `CREATE INDEX idx_tasks_title_search ON tasks USING GIN(to_tsvector('english', title))`
- [ ] Add full-text search index for description field
- [ ] Update task service with `searchTasks()` method
- [ ] Implement search using PostgreSQL `@@` operator with `ts_vector`
- [ ] Add search ranking by relevance (title matches weighted higher than description)
- [ ] Implement search highlighting (return matched snippets)
- [ ] Support multi-word queries with AND logic
- [ ] Create search endpoint: `GET /api/v1/tasks/search?q=keyword`
- [ ] Add pagination to search results
- [ ] Write unit and integration tests

**Acceptance Criteria**:
- [ ] Search matches tasks by title or description
- [ ] Multi-word queries work correctly (AND logic)
- [ ] Results ranked by relevance (title > description)
- [ ] Search case-insensitive
- [ ] Pagination works for search results
- [ ] Minimum 2 characters required for search
- [ ] Search queries complete in <300ms (95th percentile)
- [ ] All tests pass with 80%+ coverage

**Technical Notes**:
- Use PostgreSQL's `to_tsvector` and `to_tsquery` functions
- Create composite GIN index for both title and description
- Consider using pg_trgm extension for fuzzy matching (post-MVP)
- Debounce search on frontend (300ms)

**Files to Create**:
- `api/src/services/task.service.ts` (updated with searchTasks)
- `api/src/controllers/task.controller.ts` (updated with search endpoint)
- `api/prisma/migrations/YYYYMMDDHHMMSS_add_search_indexes/migration.sql`
- `api/src/__tests__/services/task.service.search.test.ts`

---

### TASK-032: Search UI Component (Frontend)
**ID**: TASK-032
**Complexity**: M (Medium)
**Effort**: 5 hours
**Dependencies**: TASK-031 (API contract defined)
**Priority**: Medium (MVP Nice-to-Have)
**Assignee Profile**: Frontend developer
**Can Run in Parallel**: Yes (after API contract is defined)

**Description**: Create search bar component with real-time results, highlighting, and keyboard shortcuts.

**Subtasks**:
- [ ] Create `/frontend/src/components/tasks/SearchBar.tsx`
- [ ] Add search input in header with icon
- [ ] Implement debounced search (300ms delay)
- [ ] Fetch search results using React Query
- [ ] Display results in dropdown with task titles highlighted
- [ ] Show loading spinner during search
- [ ] Handle empty results state ("No tasks found")
- [ ] Clicking result opens task detail modal
- [ ] Add keyboard shortcut "/" to focus search
- [ ] Clear search when Escape pressed
- [ ] Write component tests

**Acceptance Criteria**:
- [ ] Search input debounces at 300ms
- [ ] Results update in real-time as user types
- [ ] Matching keywords highlighted in results
- [ ] Loading state shown during search
- [ ] Empty state shown when no results
- [ ] Clicking result opens task detail
- [ ] "/" keyboard shortcut focuses search
- [ ] Escape clears search and closes dropdown
- [ ] Component tests cover search flow

**Technical Notes**:
- Use React Query with `enabled` option tied to query length > 2
- Highlight matches with `<mark>` tag or custom highlighting
- Use Downshift or Combobox pattern for accessible search
- Consider recent searches or suggestions (post-MVP)

**Files to Create**:
- `frontend/src/components/tasks/SearchBar.tsx`
- `frontend/src/components/tasks/SearchResults.tsx`
- `frontend/src/hooks/useTaskSearch.ts`
- `frontend/src/__tests__/components/tasks/SearchBar.test.tsx`

---

### TASK-033: Advanced Sorting Options (Backend & Frontend)
**ID**: TASK-033
**Complexity**: S (Small)
**Effort**: 4 hours
**Dependencies**: TASK-016
**Priority**: Medium (MVP Nice-to-Have)
**Assignee Profile**: Full-stack developer

**Description**: Implement multi-field sorting with ascending/descending order for task list.

**Subtasks**:
- [ ] Update task service to accept `sort` query param (e.g., `sort=due_date:asc,priority:desc`)
- [ ] Support sorting by: created_at, updated_at, due_date, priority, title, status
- [ ] Implement multi-field sorting (primary and secondary sort)
- [ ] Add sorting logic to Prisma query with `orderBy`
- [ ] Create `/frontend/src/components/tasks/SortDropdown.tsx`
- [ ] Add sort options: "Newest First", "Oldest First", "Due Date", "Priority", "Title (A-Z)"
- [ ] Display active sort option in UI
- [ ] Persist sort preference in URL params
- [ ] Write tests for sorting logic

**Acceptance Criteria**:
- [ ] Tasks sorted correctly by all supported fields
- [ ] Multi-field sorting works (e.g., priority desc, then due_date asc)
- [ ] Sort dropdown shows all options
- [ ] Active sort option highlighted
- [ ] Sort preference persisted in URL
- [ ] Sorting updates task list immediately
- [ ] Tests verify all sort combinations

**Technical Notes**:
- Use URL query params for sort state
- Default sort: `created_at:desc`
- Validate sort fields on backend to prevent SQL injection
- Consider custom sort orders (user-defined - post-MVP)

**Files to Create**:
- `api/src/utils/sorting.ts`
- `frontend/src/components/tasks/SortDropdown.tsx`
- `api/src/__tests__/utils/sorting.test.ts`

---

### TASK-034: Saved Views/Filters (Optional - Post-MVP)
**ID**: TASK-034
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-029
**Priority**: Low (Post-MVP Enhancement)
**Assignee Profile**: Full-stack developer

**Description**: Allow users to save custom filter combinations as named views for quick access.

**Subtasks**:
- [ ] Create `SavedView` database model (user_id, name, filters JSON)
- [ ] Implement saved view CRUD service and routes
- [ ] Create "Save current view" button in UI
- [ ] Display saved views in sidebar
- [ ] Allow deleting saved views
- [ ] Apply saved view filters when clicked
- [ ] Write tests for saved views

**Acceptance Criteria**:
- [ ] Users can save current filter state with custom name
- [ ] Saved views appear in sidebar
- [ ] Clicking saved view applies all filters
- [ ] Saved views can be deleted
- [ ] Saved views persist across sessions

**Technical Notes**:
- Store filter state as JSON in database
- Limit to 10 saved views per user
- Consider sharing saved views with teams (post-MVP v2)

**Files to Create**:
- `api/src/services/savedView.service.ts`
- `frontend/src/components/lists/SavedViews.tsx`

---

### TASK-035: Search & Filtering Integration Testing
**ID**: TASK-035
**Complexity**: S (Small)
**Effort**: 3 hours
**Dependencies**: TASK-032
**Priority**: Medium (Quality Gate)
**Assignee Profile**: Frontend or backend developer

**Description**: Write end-to-end tests for search functionality and advanced filtering.

**Subtasks**:
- [ ] Write E2E test: "User can search tasks by keyword"
- [ ] Write E2E test: "Search highlights matching text"
- [ ] Write E2E test: "User can sort tasks by different fields"
- [ ] Write E2E test: "Multi-field sorting works correctly"
- [ ] Write E2E test: "Search + filters combine correctly"
- [ ] Add tests to CI/CD pipeline

**Acceptance Criteria**:
- [ ] All E2E tests pass locally and in CI
- [ ] Tests cover search with various keywords
- [ ] Tests verify sorting correctness
- [ ] Tests confirm search + filter combination

**Technical Notes**:
- Seed database with diverse task data for comprehensive testing
- Test edge cases: empty search, special characters, very long queries

**Files to Create**:
- `e2e/tests/search.spec.ts`

---

## Phase 6: UI Polish & Testing

**Duration**: 7 days
**Effort**: 56-80 hours
**Goal**: Finalize UI, implement responsive design, accessibility, and comprehensive testing

---

### TASK-036: Responsive Design Implementation
**ID**: TASK-036
**Complexity**: L (Large)
**Effort**: 10 hours
**Dependencies**: TASK-021
**Priority**: High (MVP Critical)
**Assignee Profile**: Frontend developer

**Description**: Ensure all components are fully responsive across mobile, tablet, and desktop with mobile-first approach.

**Subtasks**:
- [ ] Audit all components on mobile (375px), tablet (768px), desktop (1920px)
- [ ] Implement mobile hamburger menu for sidebar navigation
- [ ] Convert desktop modals to full-screen on mobile
- [ ] Make task cards stack vertically on mobile
- [ ] Ensure touch-friendly tap targets (min 44x44px)
- [ ] Test horizontal scrolling issues
- [ ] Implement responsive typography (fluid font sizes)
- [ ] Add swipe gestures for mobile (optional - delete task swipe)
- [ ] Test on real devices (iOS Safari, Android Chrome)
- [ ] Fix any layout breaks

**Acceptance Criteria**:
- [ ] All pages render correctly on mobile, tablet, desktop
- [ ] Sidebar collapses to hamburger menu on mobile
- [ ] Forms usable on mobile without zooming
- [ ] Tap targets meet 44x44px minimum
- [ ] No horizontal scrolling on any viewport
- [ ] Typography scales appropriately
- [ ] Tested on iOS Safari and Android Chrome
- [ ] No layout shifts or broken UI elements

**Technical Notes**:
- Use TailwindCSS responsive utilities (sm:, md:, lg:, xl:)
- Test on Chrome DevTools device emulator
- Use BrowserStack for real device testing (optional)
- Consider PWA manifest for "Add to Home Screen" (post-MVP)

**Files to Create/Update**:
- `frontend/src/components/layout/MobileMenu.tsx`
- Update all component styles for responsiveness

---

### TASK-037: Accessibility (A11y) Audit & Fixes
**ID**: TASK-037
**Complexity**: M (Medium)
**Effort**: 8 hours
**Dependencies**: TASK-036
**Priority**: High (MVP Critical - NFR-005)
**Assignee Profile**: Frontend developer with A11y knowledge

**Description**: Conduct accessibility audit and implement WCAG 2.1 Level AA compliance across all components.

**Subtasks**:
- [ ] Run Axe DevTools scan on all pages
- [ ] Add ARIA labels to all interactive elements
- [ ] Implement keyboard navigation for all features (Tab, Enter, Escape, Arrows)
- [ ] Add focus indicators (visible outline on focused elements)
- [ ] Ensure color contrast ratios meet WCAG AA (4.5:1 for text)
- [ ] Add alt text to all images/icons
- [ ] Implement skip-to-content link for keyboard users
- [ ] Test with screen reader (NVDA or VoiceOver)
- [ ] Add semantic HTML (header, nav, main, footer)
- [ ] Fix any violations found in Axe scan
- [ ] Document accessibility features in README

**Acceptance Criteria**:
- [ ] Axe DevTools reports zero violations
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible on all focusable elements
- [ ] Color contrast ratios ≥4.5:1 for normal text, ≥3:1 for large text
- [ ] Screen reader announces all UI changes correctly
- [ ] ARIA labels descriptive and accurate
- [ ] Skip-to-content link functional
- [ ] Semantic HTML used throughout
- [ ] Accessibility documented

**Technical Notes**:
- Use Axe DevTools browser extension for automated testing
- Test with NVDA (Windows) or VoiceOver (Mac)
- Use headlessUI components for accessible primitives
- Add `aria-live` regions for dynamic content updates

**Files to Create/Update**:
- `docs/ACCESSIBILITY.md`
- Update all components with ARIA attributes

---

### TASK-038: Loading States & Error Handling UI
**ID**: TASK-038
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-017
**Priority**: High (MVP Critical - NFR-005)
**Assignee Profile**: Frontend developer

**Description**: Implement consistent loading states, error boundaries, and user-friendly error messages across the application.

**Subtasks**:
- [ ] Create loading skeleton components for task list, task detail
- [ ] Add loading spinners for buttons during async operations
- [ ] Create error boundary component for React errors
- [ ] Implement global error toast notification system
- [ ] Create user-friendly error messages (map API errors to readable text)
- [ ] Add retry buttons for failed requests
- [ ] Implement offline detection and warning banner
- [ ] Add success notifications for CRUD operations
- [ ] Test all error scenarios (network failure, validation errors, 500 errors)
- [ ] Write component tests for error states

**Acceptance Criteria**:
- [ ] Loading skeletons shown during data fetching
- [ ] Buttons show loading spinner during operations
- [ ] Error boundary catches and displays React errors gracefully
- [ ] Toast notifications shown for all errors and successes
- [ ] Error messages are user-friendly (no technical jargon)
- [ ] Retry buttons work correctly
- [ ] Offline banner appears when network disconnected
- [ ] All error scenarios tested and handled

**Technical Notes**:
- Use react-hot-toast or similar for toast notifications
- Create reusable Skeleton component with shimmer animation
- Map HTTP status codes to user messages (400 → validation, 401 → auth, 500 → server error)
- Use React Query's `onError` callbacks for global error handling

**Files to Create**:
- `frontend/src/components/shared/ErrorBoundary.tsx`
- `frontend/src/components/shared/Skeleton.tsx`
- `frontend/src/components/shared/Toast.tsx`
- `frontend/src/utils/errorMessages.ts`

---

### TASK-039: Performance Optimization
**ID**: TASK-039
**Complexity**: M (Medium)
**Effort**: 8 hours
**Dependencies**: TASK-036
**Priority**: High (MVP Critical - NFR-001)
**Assignee Profile**: Full-stack developer

**Description**: Optimize frontend bundle size, implement code splitting, and ensure performance targets met (<2s load, <200ms API).

**Subtasks**:
- [ ] Analyze bundle size with Vite's build analyzer
- [ ] Implement route-based code splitting for all pages
- [ ] Lazy load heavy components (modals, date picker)
- [ ] Optimize images (WebP format, lazy loading)
- [ ] Add service worker for static asset caching (optional)
- [ ] Minimize and tree-shake dependencies
- [ ] Configure React Query cache settings (staleTime, cacheTime)
- [ ] Implement virtualization for task list (react-window)
- [ ] Add database query analysis (EXPLAIN) for slow queries
- [ ] Run Lighthouse audit and fix performance issues
- [ ] Set up Lighthouse CI in GitHub Actions

**Acceptance Criteria**:
- [ ] Initial JS bundle <200KB gzipped
- [ ] Lighthouse performance score >90
- [ ] First Contentful Paint <1.5s
- [ ] Time to Interactive <3s
- [ ] API response times <200ms (p95)
- [ ] Task list handles 1,000+ tasks smoothly
- [ ] No blocking main thread >50ms
- [ ] Lighthouse CI runs on every PR

**Technical Notes**:
- Use Vite's `rollupOptions.output.manualChunks` for code splitting
- Use React.lazy and Suspense for route components
- Configure React Query `staleTime: 5 min`, `cacheTime: 30 min`
- Use `loading="lazy"` for images
- Implement memoization (React.memo, useMemo) for expensive components

**Files to Create/Update**:
- `frontend/vite.config.ts` (updated with optimization settings)
- `.github/workflows/lighthouse.yml`
- `lighthouse-budget.json`

---

### TASK-040: Unit & Integration Test Coverage
**ID**: TASK-040
**Complexity**: L (Large)
**Effort**: 12 hours
**Dependencies**: TASK-039
**Priority**: High (MVP Critical - NFR-006)
**Assignee Profile**: Backend and frontend developers

**Description**: Achieve 80% code coverage for backend and frontend with comprehensive unit and integration tests.

**Subtasks**:
- [ ] Write backend unit tests for all services (auth, task, list, tag)
- [ ] Write backend integration tests for all API routes
- [ ] Write frontend unit tests for all components (80% coverage)
- [ ] Write frontend integration tests for user flows
- [ ] Set up test coverage reporting (Vitest coverage)
- [ ] Configure coverage thresholds in CI (fail if <80%)
- [ ] Mock external dependencies (database, Redis, API)
- [ ] Test edge cases and error scenarios
- [ ] Review and improve existing tests
- [ ] Generate coverage report and badge

**Acceptance Criteria**:
- [ ] Backend code coverage ≥80%
- [ ] Frontend code coverage ≥80%
- [ ] All critical paths covered by tests
- [ ] CI fails if coverage drops below threshold
- [ ] Coverage report generated on every PR
- [ ] No flaky tests (deterministic results)
- [ ] All tests run in <3 minutes

**Technical Notes**:
- Use Vitest for both backend and frontend testing
- Use `c8` or `v8` for coverage reporting
- Mock Prisma client with `prisma-mock` or manual mocks
- Mock Axios requests with MSW (Mock Service Worker)
- Configure `vitest.config.ts` with coverage thresholds

**Files to Create**:
- `api/src/__tests__/**/*.test.ts` (comprehensive tests)
- `frontend/src/__tests__/**/*.test.tsx` (comprehensive tests)
- `vitest.config.ts` (coverage settings)

---

### TASK-041: Documentation & Developer Onboarding
**ID**: TASK-041
**Complexity**: M (Medium)
**Effort**: 6 hours
**Dependencies**: TASK-040
**Priority**: Medium (Developer Experience)
**Assignee Profile**: Any developer

**Description**: Write comprehensive documentation for setup, development, deployment, and API usage.

**Subtasks**:
- [ ] Update README with complete setup instructions
- [ ] Document environment variables in `.env.example`
- [ ] Write API documentation with OpenAPI/Swagger spec
- [ ] Create developer onboarding guide
- [ ] Document database schema and migrations
- [ ] Write deployment guide (Railway, DigitalOcean)
- [ ] Document testing strategy and how to run tests
- [ ] Add troubleshooting section to docs
- [ ] Create architecture diagram (Mermaid or draw.io)
- [ ] Document CI/CD pipeline

**Acceptance Criteria**:
- [ ] New developer can set up project in <30 minutes following README
- [ ] All environment variables documented
- [ ] API documentation complete and accurate
- [ ] Deployment guide tested and functional
- [ ] Troubleshooting covers common issues
- [ ] Architecture diagram up-to-date

**Technical Notes**:
- Use Swagger UI or Redoc for API docs
- Generate OpenAPI spec from code (tsoa or similar)
- Include example requests/responses
- Add code snippets for common tasks

**Files to Create**:
- `README.md` (updated)
- `docs/SETUP.md`
- `docs/API.md` or Swagger JSON
- `docs/DEPLOYMENT.md`
- `docs/ARCHITECTURE.md`
- `docs/TESTING.md`

---

### TASK-042: Production Deployment & Monitoring Setup
**ID**: TASK-042
**Complexity**: L (Large)
**Effort**: 10 hours
**Dependencies**: TASK-041
**Priority**: High (Deployment Critical)
**Assignee Profile**: Developer with DevOps experience

**Description**: Deploy application to production, configure monitoring, alerting, and backup systems.

**Subtasks**:
- [ ] Set up production environment on Railway.app or DigitalOcean
- [ ] Configure production database with automated backups
- [ ] Set up Redis for production (Upstash)
- [ ] Configure environment variables in production
- [ ] Set up CloudFlare CDN for static assets
- [ ] Configure custom domain and SSL certificate
- [ ] Set up UptimeRobot for uptime monitoring
- [ ] Configure Sentry for error tracking
- [ ] Set up database backup automation (daily + weekly)
- [ ] Create production deployment runbook
- [ ] Test backup restoration process
- [ ] Configure alerting (email/Slack for downtime)

**Acceptance Criteria**:
- [ ] Application accessible at production URL with SSL
- [ ] Database backups run automatically (verified)
- [ ] Uptime monitoring active with <5min check interval
- [ ] Error tracking captures and reports production errors
- [ ] CDN serves static assets with correct cache headers
- [ ] Backup restoration tested successfully
- [ ] Alerting sends notifications for downtime
- [ ] Production runbook documented

**Technical Notes**:
- Use Railway.app for easy deployment (git-push deploys)
- Configure PostgreSQL daily backups with 30-day retention
- Use CloudFlare free tier for CDN and DDoS protection
- Set up Sentry free tier for error tracking
- Configure UptimeRobot free tier (50 monitors, 5-min checks)

**Files to Create**:
- `.do/app.yaml` or `railway.toml`
- `docs/RUNBOOK.md`
- `docs/BACKUP_RESTORE.md`
- Production environment configuration

---

## Risk Assessment

### Technical Risks

| Risk ID | Risk Description | Severity | Probability | Impact | Mitigation Strategy |
|---------|------------------|----------|-------------|--------|---------------------|
| **R-001** | Database performance degrades with >100K tasks | High | Medium | Users experience slow queries (>2s) | Implement composite indexes early (TASK-003), run EXPLAIN analysis (TASK-039), test with large datasets, implement cursor-based pagination if needed |
| **R-002** | JWT token security vulnerability (XSS/CSRF) | Critical | Low | User accounts compromised, data breach | Use httpOnly cookies instead of localStorage (TASK-008), implement CSRF protection, security audit before launch, rate limiting on auth endpoints |
| **R-003** | Frontend bundle size exceeds 200KB target | Medium | Medium | Slow initial page load, poor mobile UX | Code splitting (TASK-039), lazy load components, tree-shake dependencies, monitor bundle size in CI, use Lighthouse budget |
| **R-004** | React Query cache invalidation bugs cause stale data | Medium | Medium | Users see outdated task data after updates | Thorough testing of optimistic updates (TASK-017), implement rollback on error, use React Query DevTools for debugging, clear cache on logout |
| **R-005** | PostgreSQL full-text search too slow on large datasets | Medium | Low | Search queries >300ms, poor UX | Create GIN indexes (TASK-031), benchmark with 100K+ tasks, consider ElasticSearch for post-MVP, cache popular searches in Redis |
| **R-006** | Cross-browser compatibility issues (Safari, Firefox) | Low | Medium | Features broken on specific browsers | Test on all target browsers (TASK-036), use polyfills, avoid browser-specific APIs, include browser testing in CI |
| **R-007** | Docker Compose resource consumption on dev machines | Low | Medium | Slow local development, high CPU/RAM usage | Optimize Docker images (use alpine base), document minimum system requirements, provide non-Docker setup option |
| **R-008** | Race conditions in optimistic updates | Medium | Low | UI shows incorrect state after concurrent edits | Use React Query's `onMutate`/`onError` callbacks correctly, implement version checking on backend (optional), test concurrent operations |
| **R-009** | Accessibility violations fail WCAG AA compliance | High | Medium | Legal issues, excluded user groups | Automated Axe scans in CI (TASK-037), manual screen reader testing, accessibility audit before launch, allocate time for fixes |
| **R-010** | Deployment pipeline failures block releases | Medium | Medium | Unable to ship updates, prolonged downtime | Test CI/CD pipeline early (TASK-006), implement rollback mechanism, maintain staging environment, document manual deployment process as backup |
| **R-011** | Third-party service downtime (Redis, database host) | High | Low | Application unavailable, data inaccessible | Implement health checks (TASK-005), graceful degradation (work without Redis cache), multi-region backups, choose reliable providers |
| **R-012** | Test suite becomes too slow (>5 minutes) | Low | High | Slow CI feedback, developer frustration | Parallelize tests, use test database optimization, mock external services, set time budgets per phase, profile slow tests |

### Process Risks

| Risk ID | Risk Description | Severity | Probability | Impact | Mitigation Strategy |
|---------|------------------|----------|-------------|--------|---------------------|
| **R-013** | Scope creep extends timeline beyond 12 weeks | High | High | Missed launch date, budget overrun | Strict MVP scope enforcement, defer nice-to-have features (tags, search) to post-MVP, weekly scope review, stakeholder sign-off on changes |
| **R-014** | Solo developer capacity constraint | Critical | High (solo) | Delayed tasks, burnout, quality issues | Focus on critical path tasks, parallelize after API contracts defined, use proven technologies, limit work hours to sustainable pace, skip optional tasks if needed |
| **R-015** | Underestimated task complexity | Medium | Medium | Tasks take 2x estimated time | Build 20% buffer into timeline, reassess after Phase 1, use time-boxing (stop at estimate, defer to next phase), track actual vs. estimated time |
| **R-016** | Dependency blocking (backend delays frontend) | Medium | Medium | Idle developer time, timeline slip | Define API contracts early (TASK-007), use mock APIs for frontend development, enable parallel work streams after TASK-010 |
| **R-017** | Inadequate testing coverage (<80%) | High | Medium | Bugs in production, difficult maintenance | Allocate dedicated testing phase (TASK-040), enforce coverage in CI, write tests alongside features, code review for test quality |
| **R-018** | Knowledge gaps in new technologies | Medium | Medium (solo) | Learning curve delays implementation | Proof-of-concept for unfamiliar tech (React Query, Prisma), allocate extra time for first use, have fallback technologies, leverage documentation and tutorials |

---

## Testing Strategy

### Unit Test Coverage (Target: 80%)

**Backend Unit Tests** (144 tests estimated):
- **Services** (72 tests):
  - `auth.service.ts`: 18 tests (register, login, password hashing, token generation, account lockout)
  - `task.service.ts`: 30 tests (CRUD operations, pagination, filtering, sorting, ownership validation)
  - `list.service.ts`: 12 tests (CRUD, task reassignment on delete, uniqueness constraints)
  - `tag.service.ts`: 12 tests (tag creation, autocomplete, task linking, cleanup)
- **Middleware** (24 tests):
  - `auth.middleware.ts`: 12 tests (token validation, unauthorized cases, rate limiting)
  - `validate.middleware.ts`: 12 tests (Zod validation, error formatting)
- **Utilities** (12 tests):
  - `jwt.ts`: 6 tests (token generation, verification, expiration)
  - `password.ts`: 6 tests (hashing, verification, strength validation)
- **Controllers** (36 tests):
  - Controller integration tests with mocked services

**Frontend Unit Tests** (96 tests estimated):
- **Components** (60 tests):
  - `LoginForm.tsx`: 8 tests (validation, submission, error display)
  - `TaskList.tsx`: 12 tests (rendering, empty state, loading, pagination)
  - `TaskCreateModal.tsx`: 10 tests (form submission, validation, optimistic update)
  - `TaskDetailModal.tsx`: 12 tests (view/edit mode, delete, quick actions)
  - `ListSidebar.tsx`: 8 tests (CRUD operations, task counts)
  - `SearchBar.tsx`: 10 tests (debounce, results, keyboard navigation)
- **Hooks** (24 tests):
  - `useTasks.ts`: 12 tests (query, mutations, cache invalidation)
  - `useAuth.ts`: 12 tests (login, logout, token refresh)
- **Utilities** (12 tests):
  - `dateHelpers.ts`, `validators.ts`, error handling

**Coverage Enforcement**:
- Vitest configured with `coverage.threshold`:
  - `lines: 80%`, `functions: 80%`, `branches: 75%`, `statements: 80%`
- CI fails if coverage drops below threshold
- Coverage report posted to PR as comment

---

### Integration Test Coverage

**Backend Integration Tests** (24 scenarios):
- **Authentication Flow** (6 scenarios):
  - Register → Login → Access protected route
  - Duplicate email registration fails
  - Invalid credentials fail login
  - Token expiration triggers 401
  - Rate limiting blocks excessive attempts
  - Logout invalidates token (if implemented)
- **Task CRUD Flow** (12 scenarios):
  - Create task → Retrieve → Update → Delete
  - Pagination returns correct pages
  - Filtering by status, priority, list, tags
  - Sorting by various fields
  - Search returns matching tasks
  - Cross-user access blocked (403)
- **List & Tag Management** (6 scenarios):
  - Create list → Assign task → Delete list (move tasks)
  - Add tags to task → Autocomplete → Remove tags
  - List deletion with "delete tasks" option
  - Tag cleanup after last usage removed

**Frontend Integration Tests** (React Testing Library):
- Component integration with React Query
- Form submission with API mocking (MSW)
- Error state rendering
- Loading state transitions

---

### End-to-End Test Coverage

**E2E Test Scenarios** (18 critical paths):

**Authentication** (3 scenarios):
1. User registers → auto-login → dashboard redirect
2. User logs in → dashboard → logout → redirect to login
3. Unauthenticated user accessing protected route → redirect to login

**Task Management** (8 scenarios):
4. Create task (quick-add) → appears in list
5. Create task (full form) → view detail → verify all fields
6. Edit task → save → changes reflected
7. Change task status → updates immediately
8. Delete task → confirmation → removed from list
9. Filter by status → only matching tasks shown
10. Search task → results displayed → click result → detail opens
11. Pagination → navigate pages → tasks loaded correctly

**Organization** (5 scenarios):
12. Create list → assign task → filter by list
13. Add tags to task → tag autocomplete works → tags displayed
14. Filter by priority → overdue indicator shown
15. Combine filters (status + priority + list) → correct results
16. Sort by due date → tasks in correct order

**UI/UX** (2 scenarios):
17. Mobile responsive → hamburger menu → navigate → forms usable
18. Keyboard navigation → shortcuts work → accessible

**Test Execution**:
- Playwright for E2E tests
- Run against Docker Compose environment
- Headless mode in CI, headed mode locally
- Parallel execution (4 workers)
- Target: <5 minutes total execution time

---

### Performance Test Requirements

**Frontend Performance** (Lighthouse CI):
- **Metrics**: Performance score ≥90, FCP <1.5s, TTI <3s, LCP <2.5s
- **Testing**: Automated in CI on every PR
- **Budget**: Initial bundle <200KB gzipped, total page weight <1MB

**Backend Load Testing** (k6):
```javascript
// Load test scenario
export const options = {
  stages: [
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '3m', target: 100 },   // Stay at 100 users
    { duration: '1m', target: 200 },   // Spike to 200 users
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // 95% of requests <200ms
    http_req_failed: ['rate<0.01'],    // <1% error rate
  },
};

// Test scenarios
- GET /api/v1/tasks (with filters, pagination)
- POST /api/v1/tasks
- PUT /api/v1/tasks/:id
- GET /api/v1/tasks/search?q=keyword
```

**Database Performance**:
- Query analysis with `EXPLAIN ANALYZE`
- Benchmark with 100K tasks, 1K users
- Verify index usage
- Target: <100ms for indexed queries

---

## Success Criteria Summary

### Development Metrics
- [ ] All 42 tasks completed
- [ ] 280-360 hours actual effort (within 20% of estimate)
- [ ] Code coverage ≥80% (backend + frontend)
- [ ] Zero critical bugs in production (first 2 weeks)
- [ ] CI/CD pipeline success rate ≥95%

### Quality Metrics
- [ ] Lighthouse performance score ≥90
- [ ] Axe accessibility violations = 0
- [ ] API response time p95 <200ms
- [ ] Frontend bundle size <200KB gzipped
- [ ] All NFRs from requirements.md met

### User Experience Metrics
- [ ] New user onboarding <2 minutes (registration → first task created)
- [ ] SUS (System Usability Scale) score ≥70
- [ ] Beta tester feedback ≥4.0/5.0
- [ ] Mobile usability score ≥90 (Lighthouse)

### Deployment Metrics
- [ ] Production deployment time <30 minutes (from commit to live)
- [ ] Zero-downtime deployment capability
- [ ] Automated backups verified (restore tested)
- [ ] Uptime ≥99.5% (measured over first month)

---

## Parallelization Opportunities

### Stream 1: Backend Development (Critical Path)
- TASK-001 → TASK-002 → TASK-003 → TASK-007 → TASK-008 → TASK-009 → TASK-010 → TASK-015 → TASK-016 → TASK-023 → TASK-024 → TASK-031

### Stream 2: Frontend Development (After API Contracts)
- TASK-001 → TASK-004 → TASK-011 (can start after TASK-010 defines API) → TASK-012 → TASK-013 → TASK-017 (after TASK-016) → TASK-018 → TASK-019 → TASK-020 → TASK-021 → TASK-025 (after TASK-023) → TASK-026 (after TASK-024) → TASK-027 → TASK-028 → TASK-029 → TASK-032 (after TASK-031)

### Stream 3: Infrastructure & Testing (Parallel)
- TASK-005 (parallel with TASK-003, TASK-004)
- TASK-006 (parallel with Phase 2)
- TASK-014 (after TASK-013)
- TASK-022 (after TASK-021)
- TASK-030 (after TASK-029)
- TASK-035 (after TASK-032)
- TASK-036 → TASK-037 → TASK-038 → TASK-039 → TASK-040 → TASK-041 → TASK-042

**Optimal Team Setup**:
- **1 developer**: Sequential execution, 8-12 weeks
- **2 developers**: Backend + Frontend parallel, 4-6 weeks (after Phase 1 complete)
- **3 developers**: Backend + Frontend + Testing/Infrastructure parallel, 3-4 weeks

---

## Implementation Notes

### Daily Workflow Recommendations

**Morning Routine** (15 min):
- Review yesterday's completed tasks
- Check CI/CD pipeline status
- Plan today's tasks (max 2-3 per day)
- Identify blockers

**Development Block** (2-3 hours):
- Focus on single task
- Write tests first (TDD for critical logic)
- Commit frequently (atomic commits)
- Update task status in tracking system

**Code Review** (30-60 min):
- Self-review before pushing
- Address linting/formatting issues
- Run tests locally
- Create PR with clear description

**End of Day** (15 min):
- Update task status
- Document blockers or learnings
- Plan next day's tasks

### Git Commit Standards

**Commit Message Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `style`
**Scope**: `auth`, `tasks`, `lists`, `tags`, `ui`, `api`, `db`, `ci`

**Examples**:
```
feat(auth): implement JWT authentication service (TASK-008)

- Add bcrypt password hashing
- Implement token generation
- Add account lockout logic

Closes #8
```

```
fix(tasks): correct pagination offset calculation (TASK-015)

- Fix off-by-one error in pagination
- Add unit tests for edge cases

Related to TASK-015
```

### Code Review Checklist

- [ ] Tests included and passing (unit + integration)
- [ ] Code follows project style guide (ESLint + Prettier)
- [ ] No console.log or debug code
- [ ] Error handling implemented
- [ ] TypeScript types complete (no `any` without justification)
- [ ] Performance impact considered (no obvious bottlenecks)
- [ ] Accessibility requirements met (if UI changes)
- [ ] Documentation updated (if public API changes)
- [ ] No security vulnerabilities introduced

---

## Appendix: Task Estimation Methodology

### Complexity Levels

**Small (S)**: 2-4 hours
- Single component or function
- Clear requirements, minimal unknowns
- Minimal dependencies
- Examples: TASK-007 (shared types), TASK-027 (badges)

**Medium (M)**: 4-8 hours
- Multiple related components or functions
- Some complexity or unknowns
- Moderate dependencies
- Examples: TASK-009 (auth middleware), TASK-017 (React Query hooks)

**Large (L)**: 8-12 hours
- Complex feature with multiple parts
- Significant unknowns or new technology
- Many dependencies or integrations
- Examples: TASK-008 (auth service), TASK-018 (task list), TASK-042 (deployment)

### Estimation Factors

**Time Multipliers**:
- New technology: +50%
- High uncertainty: +30%
- Critical path (no parallelization): +20%
- Testing overhead: +25% (built into estimates)

**Assumptions**:
- Developer has moderate experience with stack (React, Node.js, TypeScript)
- Access to documentation and AI assistance
- Minimal interruptions during development blocks
- Code review turnaround <24 hours

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Author**: Implementation Planning Specialist (Claude)
**Status**: Ready for Review
**Related Documents**: requirements.md, architecture.md

**Next Steps**:
1. Review and validate task breakdown with development team
2. Assign complexity ratings to each task
3. Create sprint plan (2-week sprints recommended)
4. Set up task tracking in GitHub Projects or similar
5. Begin Phase 1: Project Setup & Infrastructure

---

**END OF IMPLEMENTATION TASKS DOCUMENT**

*Total Tasks: 42*
*Total Estimated Effort: 280-360 hours*
*Target Timeline: 8-12 weeks (solo developer)*
