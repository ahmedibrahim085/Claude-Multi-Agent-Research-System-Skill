# ADR-002: Frontend Framework (React + TypeScript)

**Status**: Accepted

**Date**: 2025-11-19

**Deciders**: Technical Lead, Frontend Developer

**Tags**: frontend, framework, typescript, ui

---

## Context

TaskFlow requires a modern, interactive single-page application (SPA) for the frontend. The framework must:

1. Support complex UI interactions (task lists, filters, modals, drag-and-drop)
2. Handle client-side state management (tasks, filters, user session)
3. Provide excellent developer experience (fast development, debugging tools)
4. Enable solo developer productivity (minimal boilerplate, good documentation)
5. Meet performance requirements (<2s initial load, <3s Time to Interactive)
6. Support TypeScript for type safety across frontend and backend
7. Have a large ecosystem for UI components, tooling, and libraries
8. Be easy to recruit for (if team grows) or transfer knowledge

**Key Requirements**:
- **Performance**: <200KB gzipped initial bundle, fast re-renders
- **Developer Experience**: Hot module replacement, component dev tools, debugging
- **Browser Support**: Chrome, Firefox, Safari, Edge (latest 2 versions)
- **Mobile Friendly**: Responsive design, touch-friendly interactions
- **Accessibility**: WCAG 2.1 AA compliance, screen reader support

---

## Decision

We will use **React 18 + TypeScript 5 + Vite 5** as the frontend stack for TaskFlow.

**Build Tool**: Vite 5 (for fast development and optimized builds)
**Styling**: TailwindCSS 3 (for rapid UI development)
**State Management**: Zustand (see ADR-005)
**Data Fetching**: React Query 5 (for server state management)

---

## Rationale

### Why React 18?

#### 1. **Largest Ecosystem & Community**
- **npm Downloads**: 20M+ weekly (vs Vue 4M, Angular 3M, Svelte 400K)
- **Component Libraries**: Material-UI, Ant Design, Chakra UI, Headless UI, Radix UI
- **Developers**: Largest talent pool (easier to hire or collaborate)
- **Learning Resources**: Thousands of tutorials, courses, Stack Overflow answers
- **Longevity**: Backed by Meta (Facebook), stable future

**Impact**: Solo developers can leverage pre-built components instead of building from scratch.

#### 2. **Component Reusability & Composition**
React's component model enables DRY code:

```tsx
// Reusable Button component
<Button variant="primary" onClick={handleClick}>
  Save Task
</Button>

// Composed TaskCard component
<TaskCard>
  <TaskCard.Title>{task.title}</TaskCard.Title>
  <TaskCard.Meta>
    <PriorityBadge priority={task.priority} />
    <StatusBadge status={task.status} />
  </TaskCard.Meta>
  <TaskCard.Actions>
    <Button variant="ghost">Edit</Button>
    <Button variant="danger">Delete</Button>
  </TaskCard.Actions>
</TaskCard>
```

**Benefit**: Build once, use everywhere (task lists, detail views, search results)

#### 3. **TypeScript Integration**
React has first-class TypeScript support:

```tsx
// Props are fully typed
interface TaskListProps {
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  filters: TaskFilters;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, onTaskClick, filters }) => {
  // Autocomplete works perfectly
  return tasks.map(task => (
    <TaskCard
      key={task.id}
      task={task}  // Type-checked: must match Task interface
      onClick={() => onTaskClick(task)}
    />
  ));
};

// Type errors caught at compile time
<TaskList
  tasks={tasks}
  onTaskClick={handleClick}
  filters={filters}
  // ❌ Error: Property 'invalidProp' does not exist on type 'TaskListProps'
  invalidProp="test"
/>
```

**Benefit**: Catch 60%+ of bugs before runtime (type mismatches, missing props, wrong callbacks)

#### 4. **Performance (React 18 Features)**

**Automatic Batching**:
```tsx
// React 18: Both updates batched into single re-render
function handleSubmit() {
  setTitle(newTitle);
  setDescription(newDesc);
  setPriority(newPriority);
  // Only renders once, not three times
}
```

**Concurrent Rendering**:
```tsx
// Mark non-urgent updates as transitions
import { useTransition } from 'react';

const [isPending, startTransition] = useTransition();

function handleSearch(query: string) {
  // Urgent: Update input immediately
  setQuery(query);

  // Non-urgent: Defer filtering (keeps UI responsive)
  startTransition(() => {
    setFilteredTasks(filterTasks(query));
  });
}
```

**Suspense for Code Splitting**:
```tsx
// Lazy load routes to reduce initial bundle
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

<Suspense fallback={<LoadingSpinner />}>
  <SettingsPage />
</Suspense>
```

**Result**: 60fps smooth interactions, no UI blocking during heavy computations

#### 5. **Developer Experience**

**Hot Module Replacement (HMR)**:
- Edit component → see changes in <200ms (with Vite)
- State preserved across updates (no page refresh)
- CSS changes instant

**React DevTools**:
- Inspect component tree
- View props and state
- Trace re-renders
- Profile performance bottlenecks

**Error Boundaries**:
```tsx
// Graceful error handling
<ErrorBoundary fallback={<ErrorPage />}>
  <TaskList tasks={tasks} />
</ErrorBoundary>
```

#### 6. **Proven at Scale**
Used by: Facebook, Netflix, Airbnb, Uber, Reddit, Discord
- Handles millions of users
- Complex UIs (newsfeeds, video players, dashboards)
- Stable, well-tested codebase

---

### Why TypeScript 5?

#### 1. **Type Safety Across Full Stack**
```typescript
// Backend (Prisma generates these types)
import { Task, User } from '@prisma/client';

// Frontend (same types via shared package)
import { Task, User } from '@taskflow/shared-types';

// API client (types from OpenAPI spec or manual)
async function fetchTasks(): Promise<Task[]> {
  const response = await api.get<Task[]>('/tasks');
  return response.data; // Type-safe!
}
```

**Benefit**: Zero type mismatches between frontend and backend

#### 2. **IDE Autocomplete & Refactoring**
- Rename variable → all usages updated automatically
- Add property to interface → IDE shows all places to update
- Import suggestions as you type
- Inline documentation (JSDoc comments)

#### 3. **Catch Errors at Compile Time**
```typescript
// ❌ Compile error: Argument of type 'number' is not assignable to parameter of type 'string'
setTaskId(123);  // taskId is string, passed number

// ❌ Compile error: Property 'descripton' does not exist. Did you mean 'description'?
task.descripton;  // Typo caught immediately

// ❌ Compile error: Argument of type 'string' is not assignable to parameter of type 'TaskStatus'
setStatus('invalid');  // Must be 'not_started' | 'in_progress' | 'completed' | 'blocked'
```

**Impact**: 60-80% fewer runtime errors in production

#### 4. **Self-Documenting Code**
```typescript
// Before (JavaScript)
function createTask(title, desc, opts) {
  // What are opts? What fields? What types?
}

// After (TypeScript)
interface CreateTaskOptions {
  priority?: TaskPriority;
  dueDate?: Date;
  listId?: string;
  tags?: string[];
}

function createTask(
  title: string,
  description: string,
  options?: CreateTaskOptions
): Promise<Task> {
  // Clear contract, no documentation needed
}
```

---

### Why Vite 5?

#### 1. **Instant Server Start**
- Vite: <500ms (ESM-based, no bundling in dev)
- Webpack: 10-30s (bundles everything upfront)

#### 2. **Lightning Fast HMR**
- Vite: <200ms to see changes
- Webpack: 2-5s rebuild time

#### 3. **Optimized Production Builds**
- Rollup-based bundler (better tree-shaking than Webpack)
- Automatic code splitting
- Asset optimization (images, fonts)
- Modern browser targets (smaller bundles)

#### 4. **Zero Config**
```typescript
// vite.config.ts (minimal setup)
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // That's it! Everything else has sensible defaults
});
```

**Comparison**: Create React App requires 10-20 config files for similar features

---

## Alternatives Considered

### Vue 3
**Pros**:
- Smaller bundle size (~50KB vs React's ~130KB)
- Simpler learning curve
- Official router and state management (no decision fatigue)
- Better template syntax (HTML-like, easier for designers)

**Cons**:
- **Smaller ecosystem** (fewer component libraries, less Stack Overflow content)
- **Fewer developers** (harder to hire or find collaborators)
- **TypeScript support** (improving but not as mature as React)
- **Less proven at scale** (fewer large-scale production examples)

**Verdict**: ❌ **Rejected** - React's ecosystem and talent pool outweigh Vue's marginal DX improvements

---

### Svelte 4
**Pros**:
- **Smallest bundle size** (~30KB, compiles to vanilla JS)
- **No virtual DOM** (faster runtime performance)
- **Beautiful API** (reactivity is magical)
- **Great DX** (component syntax, scoped styles)

**Cons**:
- **Tiny ecosystem** (limited component libraries, few third-party tools)
- **Immature tooling** (debugging harder, fewer IDE extensions)
- **Compiler magic** (harder to debug when things go wrong)
- **Risky bet** (small community, uncertain long-term viability)

**Verdict**: ❌ **Rejected** - Too risky for solo developer, ecosystem too small

---

### Angular 16
**Pros**:
- **Batteries included** (router, HTTP client, forms, testing all official)
- **Enterprise-grade** (strong opinions, enforced structure)
- **TypeScript-first** (designed for TypeScript from day one)

**Cons**:
- **Steep learning curve** (RxJS, decorators, dependency injection, modules)
- **Verbose** (more boilerplate than React)
- **Larger bundle** (~200KB+ for basic app)
- **Overkill for MVP** (designed for large teams, over-engineered for solo dev)

**Verdict**: ❌ **Rejected** - Too complex for solo developer, slow development velocity

---

### Solid.js
**Pros**:
- **React-like syntax** (easy migration path)
- **Better performance** (fine-grained reactivity, no virtual DOM)
- **Small bundle** (~40KB)

**Cons**:
- **Very new** (v1.0 released 2021, risky for production)
- **Tiny ecosystem** (almost no component libraries)
- **Few developers** (hard to find help or hire)
- **Limited resources** (fewer tutorials, Stack Overflow answers)

**Verdict**: ❌ **Rejected** - Too new, too risky, ecosystem too immature

---

### Next.js (React Framework)
**Pros**:
- **Server-side rendering** (better SEO, faster initial load)
- **File-based routing** (convention over configuration)
- **API routes** (backend and frontend in one project)

**Cons**:
- **Overkill for SPA** (TaskFlow doesn't need SSR, it's a logged-in app)
- **Vendor lock-in** (Vercel-specific features)
- **Complexity** (server components, middleware, edge functions)
- **We already have backend** (Node.js API server, don't need Next.js API routes)

**Verdict**: ❌ **Rejected** - SPA approach simpler, SSR not needed for authenticated app

---

## Consequences

### Positive Consequences

1. **Rapid Development**
   - Reusable component library (build once, use everywhere)
   - Pre-built UI libraries (Material-UI, Headless UI)
   - Fast HMR (see changes instantly)

2. **Type Safety**
   - Shared types with backend (Prisma → TypeScript)
   - Compile-time error detection (60%+ bugs caught before runtime)
   - Refactoring confidence (rename safely, IDE shows all usages)

3. **Performance**
   - Code splitting (smaller initial bundle)
   - React Query (automatic caching, dedupe requests)
   - Concurrent rendering (smooth 60fps interactions)

4. **Future-Proof**
   - React 18+ features (Suspense, transitions, server components in future)
   - Large community (long-term support, security patches)
   - Easy to hire React developers (if team grows)

5. **Testing**
   - React Testing Library (best practices, accessibility-focused)
   - Vitest (fast test execution, Vite integration)
   - E2E tests (Playwright, Cypress)

### Negative Consequences

1. **Bundle Size**
   - React: ~130KB (vs Svelte's 30KB)
   - Initial load slightly slower than compiler-based frameworks

   **Mitigation**:
   - Code splitting (lazy load routes)
   - Tree-shaking (remove unused code)
   - Compression (gzip/brotli)
   - Target: <200KB initial bundle (achievable)

2. **Learning Curve**
   - React hooks (useState, useEffect, useCallback, useMemo)
   - Component lifecycle
   - State management patterns

   **Mitigation**:
   - Modern React is simpler (hooks > class components)
   - Excellent documentation (react.dev)
   - Numerous tutorials and courses

3. **Boilerplate for State Management**
   - React doesn't include state management (need Zustand/Redux)
   - Need to decide on patterns (prop drilling vs context vs library)

   **Mitigation**:
   - Zustand (minimal boilerplate, see ADR-005)
   - React Query (handles server state automatically)

4. **Re-render Performance**
   - Unnecessary re-renders if not optimized

   **Mitigation**:
   - React.memo for expensive components
   - useCallback/useMemo for stable references
   - React DevTools Profiler to identify bottlenecks

---

## Implementation Notes

### Project Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── tasks/
│   │   │   ├── TaskList.tsx
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskDetail.tsx
│   │   │   └── QuickAddTask.tsx
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MainLayout.tsx
│   │   └── shared/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       └── Modal.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useTasks.ts
│   │   └── useDebounce.ts
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── TasksPage.tsx
│   │   └── SettingsPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── authService.ts
│   ├── store/
│   │   ├── authStore.ts
│   │   └── uiStore.ts
│   ├── types/
│   │   ├── task.ts
│   │   └── user.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### Recommended Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.12.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.48.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0"
  }
}
```

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## Related Decisions

- **ADR-001**: Database Choice (PostgreSQL) - Shared TypeScript types via Prisma
- **ADR-005**: State Management (Zustand) - Client-side state for React app
- **ADR-006**: API Design - REST API consumed by React frontend

---

## References

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

---

**Reviewed By**: Technical Lead, Frontend Developer
**Approved**: 2025-11-19
**Next Review**: After MVP deployment (Month 3)
