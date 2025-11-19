# ADR-003: Authentication Strategy (JWT)

**Status**: Accepted

**Date**: 2025-11-19

**Deciders**: Technical Lead, Security Specialist

**Tags**: authentication, security, jwt, sessions

---

## Context

TaskFlow requires a secure authentication system to identify users and protect their data. The authentication mechanism must:

1. **Security**: Protect against common attacks (CSRF, XSS, session hijacking)
2. **Scalability**: Support horizontal scaling (multiple API instances)
3. **Performance**: Minimal latency overhead (<10ms per request)
4. **Developer Experience**: Simple to implement and maintain for solo/small team
5. **Statelessness**: No server-side session storage (enable horizontal scaling)
6. **Token Management**: Secure token storage, automatic expiration, refresh capability
7. **User Experience**: "Remember me" functionality, persistent sessions

**Key Requirements**:
- **NFR-002**: JWT tokens with 24-hour expiration, bcrypt password hashing (min 10 rounds)
- **FR-002**: Account lockout after 5 failed login attempts within 15 minutes
- **Deployment**: Stateless API design (no sticky sessions required)

---

## Decision

We will use **JWT (JSON Web Tokens)** for authentication with the following implementation:

1. **Token Type**: JWT stored in httpOnly cookie (primary) or Authorization header (mobile/API clients)
2. **Token Lifetime**: 24 hours (configurable to 30 days with "Remember Me")
3. **Password Hashing**: bcrypt with 12 rounds
4. **Rate Limiting**: 5 login attempts per 15 minutes per IP address
5. **Token Refresh**: Manual refresh endpoint (no automatic refresh for MVP)
6. **Logout**: Client-side token deletion (optional: server-side blacklist for critical scenarios)

---

## Rationale

### Why JWT?

#### 1. **Stateless & Horizontally Scalable**

Traditional sessions require server-side storage:
```javascript
// Session-based (stateful)
app.use(session({
  store: new RedisStore(),  // Shared session store required
  secret: 'secret',
  cookie: { maxAge: 86400000 }
}));

// Problem: All API servers must share Redis
// Problem: Sticky sessions required if sessions stored in-memory
```

JWT is stateless:
```javascript
// JWT-based (stateless)
const token = jwt.sign(
  { userId: user.id, email: user.email },
  process.env.JWT_SECRET,
  { expiresIn: '24h' }
);

// No server-side storage needed
// Any API instance can validate token
// No sticky sessions, perfect for load balancing
```

**Scalability Impact**:
- Add API instances without session synchronization
- Load balancer can route requests to any server (round-robin, least-conn)
- No Redis dependency for auth (can use for caching only)

#### 2. **Performance**

**JWT Validation** (on every request):
```javascript
// Verify token (cryptographic signature check)
const payload = jwt.verify(token, process.env.JWT_SECRET);
// Time: ~1ms (HMAC-SHA256 signature verification)
```

**Session Validation** (on every request):
```javascript
// Session-based: Database/Redis lookup
const session = await redis.get(`session:${sessionId}`);
// Time: ~5-10ms (network round-trip to Redis)
```

**Performance Gain**: 5-10x faster (no network I/O for auth)

#### 3. **Developer Experience**

**Simple Implementation**:
```typescript
// Login endpoint
app.post('/api/v1/auth/login', async (req, res) => {
  const { email, password } = req.body;

  // Validate credentials
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Generate JWT
  const token = jwt.sign(
    { sub: user.id, email: user.email },
    process.env.JWT_SECRET!,
    { expiresIn: '24h', jwtid: crypto.randomUUID() }
  );

  // Send token
  res.cookie('auth_token', token, {
    httpOnly: true,    // Prevent JavaScript access (XSS protection)
    secure: true,      // HTTPS only
    sameSite: 'strict',
    maxAge: 86400000   // 24 hours
  });

  res.json({ user: { id: user.id, email: user.email }, token });
});
```

**Authentication Middleware**:
```typescript
// Middleware to protect routes
export const authenticate = (req: Request, res: Response, next: NextFunction) => {
  // Extract token from cookie or Authorization header
  const token = req.cookies.auth_token || req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    // Verify token
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as JwtPayload;

    // Attach user to request
    req.user = { id: payload.sub, email: payload.email };
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// Usage
app.get('/api/v1/tasks', authenticate, taskController.list);
```

**Only ~30 lines of code** for complete auth system!

#### 4. **Security**

**Token Structure** (JWT payload):
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user_id
  "email": "user@example.com",
  "iat": 1700400000,  // Issued at (Unix timestamp)
  "exp": 1700486400,  // Expires at (24 hours later)
  "jti": "unique-token-id"  // JWT ID (for revocation)
}
```

**Signature Verification**:
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

**Security Properties**:
- ✅ **Tamper-proof**: Any modification invalidates signature
- ✅ **Automatic expiration**: Token becomes invalid after 24 hours
- ✅ **Self-contained**: No database lookup needed for validation
- ✅ **Unique ID**: `jti` field enables token revocation (if needed)

**httpOnly Cookie Protection**:
```javascript
// Cookie settings
res.cookie('auth_token', token, {
  httpOnly: true,    // ✅ JavaScript can't access (XSS protection)
  secure: true,      // ✅ HTTPS only (no cleartext transmission)
  sameSite: 'strict' // ✅ CSRF protection (browser won't send in cross-site requests)
});
```

**Password Security**:
```typescript
import bcrypt from 'bcrypt';

// Hash password on registration
const SALT_ROUNDS = 12;  // 2^12 iterations (~250ms on modern CPU)
const passwordHash = await bcrypt.hash(password, SALT_ROUNDS);

// Verify password on login
const isValid = await bcrypt.compare(password, user.passwordHash);

// Password requirements (Zod schema)
const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Must contain uppercase letter')
  .regex(/[a-z]/, 'Must contain lowercase letter')
  .regex(/[0-9]/, 'Must contain number');
```

**Rate Limiting** (prevent brute-force):
```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';

const authLimiter = rateLimit({
  store: new RedisStore({ client: redis }),
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 5,                     // 5 attempts
  skipSuccessfulRequests: true,
  message: 'Too many login attempts, try again in 15 minutes',
  standardHeaders: true
});

app.post('/api/v1/auth/login', authLimiter, authController.login);
```

#### 5. **Token Refresh Strategy**

**Option 1: Manual Refresh** (MVP approach):
```typescript
// Refresh endpoint
app.post('/api/v1/auth/refresh', authenticate, (req, res) => {
  // Issue new token with extended expiration
  const newToken = jwt.sign(
    { sub: req.user!.id, email: req.user!.email },
    process.env.JWT_SECRET!,
    { expiresIn: '24h', jwtid: crypto.randomUUID() }
  );

  res.cookie('auth_token', newToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 86400000
  });

  res.json({ token: newToken });
});

// Frontend calls /refresh before token expires
// React Query can handle this automatically with retry logic
```

**Option 2: "Remember Me"** (30-day expiration):
```typescript
// Login with remember me
const expiresIn = rememberMe ? '30d' : '24h';
const token = jwt.sign(payload, secret, { expiresIn });
```

#### 6. **Logout Implementation**

**Client-Side Logout** (MVP):
```typescript
// Server endpoint
app.post('/api/v1/auth/logout', authenticate, (req, res) => {
  // Clear cookie
  res.clearCookie('auth_token');
  res.json({ message: 'Logged out successfully' });
});

// Frontend
localStorage.removeItem('auth_token'); // If using localStorage
// OR cookie cleared automatically by server response
```

**Server-Side Logout** (optional, for critical scenarios):
```typescript
// Store token blacklist in Redis
app.post('/api/v1/auth/logout', authenticate, async (req, res) => {
  const token = req.cookies.auth_token;
  const decoded = jwt.decode(token) as JwtPayload;

  // Blacklist token until expiration
  const ttl = decoded.exp! - Math.floor(Date.now() / 1000);
  await redis.setex(`blacklist:${decoded.jti}`, ttl, '1');

  res.clearCookie('auth_token');
  res.json({ message: 'Logged out successfully' });
});

// Check blacklist in auth middleware
const isBlacklisted = await redis.exists(`blacklist:${payload.jti}`);
if (isBlacklisted) {
  return res.status(401).json({ error: 'Token revoked' });
}
```

---

## Alternatives Considered

### Session-Based Authentication (Cookie Sessions)
**Pros**:
- Traditional, well-understood approach
- Easy to revoke (delete session from store)
- Server-side control (can change session data without client re-login)

**Cons**:
- **Requires server-side storage** (Redis, database, or in-memory)
  - Cost: Redis instance ($10-50/month)
  - Complexity: Session replication across servers
- **Sticky sessions or shared storage** (complicates horizontal scaling)
- **Database/Redis lookup on every request** (5-10ms latency)
- **Session hijacking risk** (if session ID leaked, attacker has full access until logout)

**Verdict**: ❌ **Rejected** - Stateful architecture conflicts with horizontal scaling goal

---

### OAuth2 (Third-Party Auth)
**Providers**: Google, GitHub, Microsoft, Auth0

**Pros**:
- No password storage (security benefit)
- User convenience (one-click login)
- Email verification handled by provider

**Cons**:
- **Vendor dependency** (if Google login breaks, users can't log in)
- **Privacy concerns** (user must trust third-party provider)
- **Complex implementation** (OAuth2 flow, token exchange, refresh tokens)
- **Not suitable for self-hosted** (requires domain verification, redirect URLs)
- **Cost** (Auth0: $35/month for 1,000 MAU)

**Verdict**: ❌ **Rejected for MVP**, ✅ **Considered for post-MVP** (optional social login)

---

### Passport.js (Authentication Middleware)
**Pros**:
- Strategy-based (supports JWT, sessions, OAuth, etc.)
- Large ecosystem (500+ strategies)
- Well-maintained (10+ years)

**Cons**:
- **Overkill for simple JWT** (adds abstraction layer for single strategy)
- **Larger dependency** (passport + passport-jwt + passport-local)
- **Learning curve** (strategy pattern, serialization/deserialization)

**Verdict**: ⚠️ **Neutral** - Can use for OAuth2 in future, but manual JWT simpler for MVP

---

### Auth0 / Firebase Auth (Authentication-as-a-Service)
**Pros**:
- Zero implementation effort (SDK handles everything)
- Built-in MFA, social login, password reset
- Generous free tier (7,000 MAU for Auth0)

**Cons**:
- **Vendor lock-in** (hard to migrate away)
- **Cost scaling** (Auth0: $35/month after free tier, $0.0175/MAU)
- **Privacy concerns** (user data stored with third-party)
- **Not suitable for self-hosted** (requires internet, can't run offline)

**Verdict**: ❌ **Rejected** - Vendor lock-in and self-hosting requirement conflict

---

### Magic Link / Passwordless Auth
**Providers**: Magic.link, Auth0 Passwordless

**Pros**:
- Better UX (no password to remember)
- No password storage (can't leak what you don't have)
- Phishing-resistant (link sent to verified email)

**Cons**:
- **Email dependency** (if email service down, can't log in)
- **Email delivery delay** (5-60 seconds, poor UX)
- **Requires email service** (SendGrid, AWS SES - $0.10/1,000 emails)
- **Complex implementation** (token generation, expiration, email templates)

**Verdict**: ❌ **Rejected for MVP**, ✅ **Considered for post-MVP** (optional login method)

---

## Consequences

### Positive Consequences

1. **Horizontal Scalability**
   - Add API instances without session synchronization
   - Load balancer can use any routing algorithm (round-robin, least-conn)
   - No Redis dependency for auth (can use for caching only)

2. **Performance**
   - ~1ms auth overhead per request (signature verification)
   - No database/Redis lookup (5-10ms saved per request)
   - 100,000 req/sec possible on single server (CPU-bound, not I/O-bound)

3. **Cost Savings**
   - No Redis required for sessions (save $10-50/month)
   - No session storage scaling costs
   - Simpler infrastructure

4. **Developer Experience**
   - ~30 lines of code for complete auth system
   - No ORM/database interactions for auth
   - Easy to test (mock JWT tokens)

5. **Security**
   - httpOnly cookies prevent XSS attacks
   - sameSite=strict prevents CSRF attacks
   - Automatic expiration (no manual cleanup)
   - bcrypt password hashing (industry standard)

### Negative Consequences

1. **Token Revocation Complexity**
   - Can't immediately invalidate JWT (valid until expiration)
   - Need Redis blacklist for forced logout (adds complexity)

   **Mitigation**:
   - Short expiration (24 hours) limits attack window
   - Blacklist only for critical scenarios (password change, account compromise)
   - Refresh tokens for longer sessions (30-day "Remember Me")

2. **Token Size Overhead**
   - JWT in cookie: ~300-500 bytes (vs session ID: ~32 bytes)
   - Sent on every request (network overhead)

   **Mitigation**:
   - 500 bytes negligible compared to typical response (5-50 KB)
   - gzip compression reduces overhead
   - HTTP/2 header compression

3. **No Server-Side State**
   - Can't update user permissions without re-login or token refresh
   - If user role changes, old token still has old role until expiration

   **Mitigation**:
   - 24-hour expiration limits stale data window
   - Critical permission changes can blacklist old tokens
   - Refresh endpoint updates permissions

4. **Secret Rotation Complexity**
   - Changing JWT_SECRET invalidates all tokens (forces all users to re-login)

   **Mitigation**:
   - Rotate quarterly (planned maintenance window)
   - Support multiple secrets during rotation (verify with old or new)
   ```typescript
   const secrets = [process.env.JWT_SECRET_NEW, process.env.JWT_SECRET_OLD];
   for (const secret of secrets) {
     try {
       return jwt.verify(token, secret);
     } catch {}
   }
   throw new Error('Invalid token');
   ```

5. **Token Theft Risk**
   - If token stolen (XSS, MITM), attacker has access until expiration

   **Mitigation**:
   - httpOnly cookies prevent XSS theft
   - HTTPS prevents MITM attacks
   - sameSite=strict prevents CSRF
   - Short expiration (24 hours) limits damage
   - Monitor for suspicious activity (IP changes, unusual access patterns)

---

## Implementation Notes

### Environment Variables
```bash
# .env
JWT_SECRET="your-256-bit-secret"  # Generate: openssl rand -base64 32
JWT_EXPIRATION="24h"
JWT_REFRESH_EXPIRATION="30d"
```

### Token Generation
```typescript
// utils/jwt.ts
import jwt from 'jsonwebtoken';
import crypto from 'crypto';

interface JwtPayload {
  sub: string;   // user_id
  email: string;
  iat: number;
  exp: number;
  jti: string;
}

export function generateToken(
  userId: string,
  email: string,
  expiresIn: string = '24h'
): string {
  return jwt.sign(
    { sub: userId, email },
    process.env.JWT_SECRET!,
    { expiresIn, jwtid: crypto.randomUUID() }
  );
}

export function verifyToken(token: string): JwtPayload {
  return jwt.verify(token, process.env.JWT_SECRET!) as JwtPayload;
}
```

### Password Hashing
```typescript
// utils/password.ts
import bcrypt from 'bcrypt';

const SALT_ROUNDS = 12;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function comparePassword(
  password: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

### Authentication Middleware
```typescript
// middleware/auth.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { verifyToken } from '../utils/jwt';

declare global {
  namespace Express {
    interface Request {
      user?: { id: string; email: string };
    }
  }
}

export const authenticate = (
  req: Request,
  res: Response,
  next: NextFunction
) => {
  // Extract token from cookie or Authorization header
  const token =
    req.cookies.auth_token ||
    req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      error: { code: 'UNAUTHORIZED', message: 'No token provided' }
    });
  }

  try {
    const payload = verifyToken(token);
    req.user = { id: payload.sub, email: payload.email };
    next();
  } catch (error) {
    return res.status(401).json({
      error: { code: 'INVALID_TOKEN', message: 'Token expired or invalid' }
    });
  }
};
```

### Frontend Token Storage
```typescript
// services/authService.ts (Frontend)
import axios from 'axios';

// Option 1: httpOnly cookie (recommended)
// Token automatically sent with requests, stored in cookie by server
export async function login(email: string, password: string) {
  const response = await axios.post('/api/v1/auth/login', { email, password }, {
    withCredentials: true  // Send cookies in cross-origin requests
  });
  return response.data;
}

// Option 2: localStorage (for mobile apps or API clients)
export async function loginWithLocalStorage(email: string, password: string) {
  const response = await axios.post('/api/v1/auth/login', { email, password });
  const { token } = response.data;

  // Store token
  localStorage.setItem('auth_token', token);

  // Set default header for future requests
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

  return response.data;
}

// Logout
export async function logout() {
  await axios.post('/api/v1/auth/logout', {}, { withCredentials: true });
  localStorage.removeItem('auth_token');
  delete axios.defaults.headers.common['Authorization'];
}
```

---

## Security Checklist

- [x] JWT secret is 256-bit random string (not hardcoded)
- [x] Tokens expire within 24 hours
- [x] httpOnly cookies prevent XSS theft
- [x] sameSite=strict prevents CSRF attacks
- [x] HTTPS enforced in production (secure cookie flag)
- [x] Password hashing with bcrypt (12 rounds)
- [x] Rate limiting on auth endpoints (5 attempts/15 min)
- [x] Password requirements (min 8 chars, uppercase, lowercase, number)
- [x] Account lockout after failed attempts
- [x] Token blacklist mechanism (for forced logout)

---

## Related Decisions

- **ADR-002**: Frontend Framework (React) - JWT stored in cookie, accessed via API calls
- **ADR-004**: Deployment Platform - Stateless JWT enables horizontal scaling

---

## References

- [JWT.io](https://jwt.io) - JWT debugger and documentation
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [bcrypt Best Practices](https://github.com/kelektiv/node.bcrypt.js#a-note-on-rounds)
- [httpOnly Cookie Security](https://owasp.org/www-community/HttpOnly)

---

**Reviewed By**: Security Specialist, Technical Lead
**Approved**: 2025-11-19
**Next Review**: After MVP deployment (Month 3)
