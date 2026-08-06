# Architecture Patterns Reference

## 1. Project Structure — Feature-First Organization

```
✅ Feature-first                ❌ Layer-first
src/                src/
  orders/                             controllers/
    order.controller.ts                order.controller.ts
    order.service.ts                    user.controller.ts
    order.repository.ts               services/
    order.dto.ts                        order.service.ts
    order.test.ts                       user.service.ts
  users/                              repositories/
    user.controller.ts...
    user.service.ts
  shared/
    database/
    middleware/
```

## 2. Three-Layer Architecture

```
Controller (HTTP) → Service (Business Logic) → Repository (Data Access)
```

| Layer | Responsibility |❌ Never |
|-------|---------------|---------|
| Controller | Parse request, validate, call service, format response | Business logic, DB queries |
| Service | Business rules, orchestration, transaction mgmt | HTTP types (req/res), direct DB |
| Repository | Database queries, external API calls | Business logic, HTTP types |

## 3. Dependency Injection

**TypeScript:**
```typescript
class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly emailService: EmailService,
  ) {}
}
```

**Python:**
```python
class OrderService:
    def __init__(self, order_repo: OrderRepository, email_service: EmailService):
        self.order_repo = order_repo
        self.email_service = email_service
```

**Go:**
```go
type OrderService struct {
    orderRepo    OrderRepository
    emailService EmailService
}

func NewOrderService(repo OrderRepository, email EmailService) *OrderService {
    return &OrderService{orderRepo: repo, emailService: email}
}
```

## 4. Configuration — Centralized, Typed, Fail-Fast

**TypeScript:**
```typescript
const config = {
  port: parseInt(process.env.PORT || '3000', 10),
  database: { url: requiredEnv('DATABASE_URL'), poolSize: intEnv('DB_POOL_SIZE', 10) },
  auth: { jwtSecret: requiredEnv('JWT_SECRET'), expiresIn: process.env.JWT_EXPIRES_IN || '1h' },
} as const;

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required env var: ${name}`);
  return value;
}
```

**Python:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    port: int = 3000
    db_pool_size: int = 10
    class Config:
        env_file = ".env"

settings = Settings()  # fails fast if DATABASE_URL missing
```

## 5. Error Handling — Typed Hierarchy

```typescript
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly isOperational: boolean = true,
  ) { super(message); }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 'NOT_FOUND', 404);
  }
}

class ValidationError extends AppError {
  constructor(public readonly errors: FieldError[]) {
    super('Validation failed', 'VALIDATION_ERROR', 422);
  }
}
```

**Global Error Handler (Express):**
```typescript
app.use((err, req, res, next) => {
  if (err instanceof AppError && err.isOperational) {
    return res.status(err.statusCode).json({
      title: err.code, status: err.statusCode,
      detail: err.message, request_id: req.id,
    });
  }
  logger.error('Unexpected error', { error: err.message, stack: err.stack, request_id: req.id });
  res.status(500).json({ title: 'Internal Error', status: 500, request_id: req.id });
});
```

## 6. Database Access Patterns

### Migrations
```bash
# TypeScript (Prisma)           # Python (Alembic)              # Go (golang-migrate)
npx prisma migrate dev          alembic revision --autogenerate  migrate -source file://migrations
npx prisma migrate deploy       alembic upgrade head             migrate -database $DB up
```

### N+1 Prevention
```typescript
// ❌ N+1
const orders = await db.order.findMany();
for (const o of orders) { o.items = await db.item.findMany({ where: { orderId: o.id } }); }

// ✅ Single JOIN
const orders = await db.order.findMany({ include: { items: true } });
```

### Transactions
```typescript
await db.$transaction(async (tx) => {
  const order = await tx.order.create({ data: orderData });
  await tx.inventory.decrement({ productId, quantity });
  await tx.payment.create({ orderId: order.id, amount });
});
```

## 7. API Client Patterns

### Typed Fetch Wrapper
```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}
```

### React Query Integration
```typescript
export function useOrders() {
  return useQuery({
    queryKey: ['orders'],
    queryFn: () => apiClient.get<{ data: Order[] }>('/api/orders'),
    staleTime: 1000 * 60,
  });
}
```

## 8. Authentication Middleware Order

```
Request → RequestID → Logging → CORS → RateLimit → BodyParse → Auth → Authz → Validation → Handler → ErrorHandler → Response
```

### RBAC Pattern
```typescript
function authorize(...roles: Role[]) {
  return (req, res, next) => {
    if (!req.user) throw new UnauthorizedError();
    if (!roles.some(r => req.user.roles.includes(r))) throw new ForbiddenError();
    next();
  };
}
```

## 9. Real-Time Patterns

| Method | Direction | When |
|--------|-----------|------|
| Polling | Client → Server | Simple status checks |
| SSE | Server → Client | Notifications, feeds, AI streaming |
| WebSocket | Bidirectional | Chat, collaboration, gaming |

## 10. Production Hardening

### Health Checks
```typescript
app.get('/health', (req, res) => res.json({ status: 'ok' }));
app.get('/ready', async (req, res) => {
  const checks = { database: await checkDb(), redis: await checkRedis() };
  const ok = Object.values(checks).every(c => c.status === 'ok');
  res.status(ok ? 200 : 503).json({ status: ok ? 'ok' : 'degraded', checks });
});
```

### Graceful Shutdown
```typescript
process.on('SIGTERM', async () => {
  server.close();
  await drainConnections();
  await closeDatabase();
  process.exit(0);
});
```
