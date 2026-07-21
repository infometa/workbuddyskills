---
description: Implement API rate limiting
category: project-setup
---

# Setup Rate Limiting

Implement API rate limiting

## Instructions

1. **Rate Limiting Strategy and Planning**
   - Analyze API endpoints and traffic patterns
   - Define rate limiting policies for different user types and endpoints
   - Plan for distributed rate limiting across multiple servers
   - Consider different rate limiting algorithms (token bucket, sliding window, etc.)
   - Design rate limiting bypass mechanisms for trusted clients

2. **Express.js Rate Limiting Implementation**
   - Set up comprehensive rate limiting middleware:

   **Basic Rate Limiting Setup:**
   ```javascript
   // middleware/rate-limiter.js
   const rateLimit = require('express-rate-limit');
   const RedisStore = require('rate-limit-redis');
   const Redis = require('ioredis');

   class RateLimiter {
     constructor() {
       this.redis = new Redis(process.env.REDIS_URL);
       this.setupDefaultLimiters();
     }

     setupDefaultLimiters() {
       // General API rate limiter
       this.generalLimiter = rateLimit({
         store: new RedisStore({
           sendCommand: (...args) => this.redis.call(...args),
         }),
         windowMs: 15 * 60 * 1000, // 15 minutes
         max: 1000, // Limit each IP to 1000 requests per windowMs
         message: {
           error: 'Too many requests from this IP',
           retryAfter: '15 minutes'
         },
         standardHeaders: true,
         legacyHeaders: false,
         keyGenerator: (req) => {
           // Use user ID if authenticated, otherwise IP
           return req.user?.id || req.ip;
         },
         skip: (req) => {
           // Skip rate limiting for internal requests
           return req.headers['x-internal-request'] === 'true';
         },
         onLimitReached: (req, res, options) => {
           console.warn('Rate limit reached:', {
             ip: req.ip,
             userAgent: req.get('User-Agent'),
             endpoint: req.path,
             timestamp: new Date().toISOString()
           });
         }
       });

       // Strict limiter for sensitive endpoints
       this.strictLimiter = rateLimit({
         store: new RedisStore({
           sendCommand: (...args) => this.redis.call(...args),
         }),
         windowMs: 60 * 60 * 1000, // 1 hour
         max: 5, // Very strict limit
         message: {
           error: 'Too many attempts for this sensitive operation',
           retryAfter: '1 hour'
         },
         skipSuccessfulRequests: true,
         keyGenerator: (req) => `${req.user?.id || req.ip}:${req.path}`
       });

       // Authentication rate limiter
       this.authLimiter = rateLimit({
         store: new RedisStore({
           sendCommand: (...args) => this.redis.call(...args),
         }),
         windowMs: 15 * 60 * 1000, // 15 minutes
         max: 5, // Limit login attempts
         skipSuccessfulRequests: true,
         keyGenerator: (req) => `auth:${req.ip}:${req.body.email || req.body.username}`,
         message: {
           error: 'Too many authentication attempts',
           retryAfter: '15 minutes'
         }
       });
     }

     // Dynamic rate limiter based on user tier
     createTierBasedLimiter(windowMs = 15 * 60 * 1000) {
       return rateLimit({
         store: new RedisStore({
           sendCommand: (...args) => this.redis.call(...args),
         }),
         windowMs,
         max: (req) => {
           const user = req.user;
           if (!user) return 100; // Anonymous users
           
           switch (user.tier) {
             case 'premium': return 10000;
             case 'pro': return 5000;
             case 'basic': return 1000;
             default: return 500;
           }
         },
         keyGenerator: (req) => `tier:${req.user?.id || req.ip}`,
         message: (req) => ({
           error: 'Rate limit exceeded for your tier',
           currentTier: req.user?.tier || 'anonymous',
           upgradeUrl: '/upgrade'
         })
       });
     }

     // Endpoint-specific rate limiter
     createEndpointLimiter(endpoint, config) {
       return rateLimit({
         store: new RedisStore({
           sendCommand: (...args) => this.redis.call(...args),
         }),
         windowMs: config.windowMs || 60 * 1000,
         max: config.max || 100,
         keyGenerator: (req) => `endpoint:${endpoint}:${req.user?.id || req.ip}`,
         message: {
           error: `Rate limit exceeded for ${endpoint}`,
           limit: config.max,
           window: config.windowMs
         },
         ...config
       });
     }
   }

   module.exports = new RateLimiter();
   ```

3. **Advanced Rate Limiting Algorithms**
   - Implement sophisticated rate limiting strategies:

   **Token Bucket Implementation:**
   ```javascript
   // rate-limiters/token-bucket.js
   class TokenBucket {
     constructor(capacity, refillRate, refillPeriod = 1000) {
       this.capacity = capacity;
       this.tokens = capacity;
       this.refillRate = refillRate;
       this.refillPeriod = refillPeriod;
       this.lastRefill = Date.now();
     }

     consume(tokens = 1) {
       this.refill();
       
       if (this.tokens >= tokens) {
         this.tokens -= tokens;
         return true;
       }
       
       return false;
     }

     refill() {
       const now = Date.now();
       const timePassed = now - this.lastRefill;
       const tokensToAdd = Math.floor(timePassed / this.refillPeriod) * this.refillRate;
       
       this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
       this.lastRefill = now;
     }

     getAvailableTokens() {
       this.refill();
       return this.tokens;
     }

     getTimeToNextToken() {
       if (this.tokens > 0) return 0;
       
       const timeSinceLastRefill = Date.now() - this.lastRefill;
       return this.refillPeriod - (timeSinceLastRefill % this.refillPeriod);
     }
   }

   // Redis-backed token bucket for distributed systems
   class DistributedTokenBucket {
     constructor(redis, key, capacity, refillRate, refillPeriod = 1000) {
       this.redis = redis;
       this.key = key;
       this.capacity = capacity;
       this.refillRate = refillRate;
       this.refillPeriod = refillPeriod;
     }

     async consume(tokens = 1) {
       const script = `
         local key = KEYS[1]
         local capacity = tonumber(ARGV[1])
         local refillRate = tonumber(ARGV[2])
         local refillPeriod = tonumber(ARGV[3])
         local tokensRequested = tonumber(ARGV[4])
         local now = tonumber(ARGV[5])
         
         local bucket = redis.call('HMGET', key, 'tokens', 'lastRefill')
         local tokens = tonumber(bucket[1]) or capacity
         local lastRefill = tonumber(bucket[2]) or now
         
         -- Calculate tokens to add
         local timePassed = now - lastRefill
         local tokensToAdd = math.floor(timePassed / refillPeriod) * refillRate
         tokens = math.min(capacity, tokens + tokensToAdd)
         
         local success = 0
         if tokens >= tokensRequested then
           tokens = tokens - tokensRequested
           success = 1
         end
         
         -- Update bucket
         redis.call('HMSET', key, 'tokens', tokens, 'lastRefill', now)
         redis.call('EXPIRE', key, 3600) -- 1 hour TTL
         
         return {success, tokens, math.max(0, refillPeriod - (timePassed % refillPeriod))}
       `;

       const result = await this.redis.eval(
         script,
         1,
         this.key,
         this.capacity,
         this.refillRate,
         this.refillPeriod,
         tokens,
         Date.now()
       );

       return {
         allowed: result[0] === 1,
         tokensRemaining: result[1],
         timeToNextToken: result[2]
       };
     }
   }

   module.exports = { TokenBucket, DistributedTokenBucket };
   ```

   **Sliding Window Rate Limiter:**
   ```javascript
   // rate-limiters/sliding-window.js
   class SlidingWindowRateLimiter {
     constructor(redis, windowSize, maxRequests) {
       this.redis = redis;
       this.windowSize = windowSize; // in milliseconds
       this.maxRequests = maxRequests;
     }

     async isAllowed(key) {
       const now = Date.now();
       const windowStart = now - this.windowSize;

       const script = `
         local key = KEYS[1]
         local windowStart = tonumber(ARGV[1])
         local now = tonumber(ARGV[2])
         local maxRequests = tonumber(ARGV[3])
         
         -- Remove old entries
         redis.call('ZREMRANGEBYSCORE', key, 0, windowStart)
         
         -- Count current requests in window
         local currentCount = redis.call('ZCARD', key)
         
         if currentCount < maxRequests then
           -- Add current request
           redis.call('ZADD', key, now, now)
           redis.call('EXPIRE', key, math.ceil(ARGV[4] / 1000))
           return {1, currentCount + 1, maxRequests - currentCount - 1}
         else
           return {0, currentCount, 0}
         end
       `;

       const result = await this.redis.eval(
         script,
         1,
         key,
         windowStart,
         now,
         this.maxRequests,
         this.windowSize
       );

       return {
         allowed: result[0] === 1,
         currentCount: result[1],
         remaining: result[2]
       };
     }

     async getRemainingRequests(key) {
       const now = Date.now();
       const windowStart = now - this.windowSize;
       
       await this.redis.zremrangebyscore(key, 0, windowStart);
       const currentCount = await this.redis.zcard(key);
       
       return Math.max(0, this.maxRequests - currentCount);
     }
   }

   module.exports = SlidingWindowRateLimiter;
   ```

4. **Custom Rate Limiting Middleware**
   - Build flexible rate limiting solutions:

   **Advanced Rate Limiting Middleware:**
   ```javascript
   // middleware/advanced-rate-limiter.js
   const { TokenBucket, DistributedTokenBucket } = require('../rate-limiters/token-bucket');
   const SlidingWindowRateLimiter = require('../rate-limiters/sliding-window');

   class AdvancedRateLimiter {
     constructor(redis) {
       this.redis = redis;
       this.rateLimiters = new Map();
       this.setupRateLimiters();
     }

     setupRateLimiters() {
       // API endpoints with different limits
       this.rateLimiters.set('api:general', {
         type: 'sliding-window',
         limiter: new SlidingWindowRateLimiter(this.redis, 60000, 1000) // 1000 req/min
       });

       this.rateLimiters.set('api:upload', {
         type: 'token-bucket',
         capacity: 10,
         refillRate: 1,
         refillPeriod: 10000 // 1 token per 10 seconds
       });

       this.rateLimiters.set('api:search', {
         type: 'sliding-window',
         limiter: new SlidingWindowRateLimiter(this.redis, 60000, 100) // 100 req/min
       });
     }

     createMiddleware(limiterKey, options = {}) {
       return async (req, res, next) => {
         try {
           const userKey = this.generateUserKey(req, limiterKey);
           const config = this.rateLimiters.get(limiterKey);

           if (!config) {
             return next(); // No rate limiting configured
           }

           let result;
           
           if (config.type === 'sliding-window') {
             result = await config.limiter.isAllowed(userKey);
           } else if (config.type === 'token-bucket') {
             const bucket = new DistributedTokenBucket(
               this.redis,
               userKey,
               config.capacity,
               config.refillRate,
               config.refillPeriod
             );
             result = await bucket.consume(options.tokensRequired || 1);
           }

           // Set rate limit headers
           this.setRateLimitHeaders(res, result, config);

           if (!result.allowed) {
             return res.status(429).json({
               error: 'Rate limit exceeded',
               retryAfter: this.calculateRetryAfter(result, config),
               remaining: result.remaining || 0
             });
           }

           // Add rate limit info to request
           req.rateLimit = result;
           next();

         } catch (error) {
           console.error('Rate limiting error:', error);
           next(); // Fail open - don't block requests on rate limiter errors
         }
       };
     }

     generateUserKey(req, limiterKey) {
       const userId = req.user?.id || req.ip;
       const endpoint = req.route?.path || req.path;
       return `${limiterKey}:${userId}:${endpoint}`;
     }

     setRateLimitHeaders(res, result, config) {
       if (result.remaining !== undefined) {
         res.set('X-RateLimit-Remaining', result.remaining.toString());
       }
       
       if (result.currentCount !== undefined) {
         res.set('X-RateLimit-Used', result.currentCount.toString());
       }

       if (config.type === 'sliding-window') {
         res.set('X-RateLimit-Limit', config.limiter.maxRequests.toString());
         res.set('X-RateLimit-Window', (config.limiter.windowSize / 1000).toString());
       } else if (config.type === 'token-bucket') {
         res.set('X-RateLimit-Limit', config.capacity.toString());
       }
     }

     calculateRetryAfter(result, config) {
       if (result.timeToNextToken) {
         return Math.ceil(result.timeToNextToken / 1000);
       }
       
       if (config.type === 'sliding-window') {
         return Math.ceil(config.limiter.windowSize / 1000);
       }
       
       return 60; // Default 1 minute
     }

     // Dynamic rate limiting based on system load
     createAdaptiveLimiter(baseLimit) {
       return async (req, res, next) => {
         const systemLoad = await this.getSystemLoad();
         let dynamicLimit = baseLimit;

         // Reduce limits during high load
         if (systemLoad > 0.8) {
           dynamicLimit = Math.floor(baseLimit * 0.5);
         } else if (systemLoad > 0.6) {
           dynamicLimit = Math.floor(baseLimit * 0.7);
         }

         // Apply dynamic limit
         const limiter = new SlidingWindowRateLimiter(this.redis, 60000, dynamicLimit);
         const userKey = this.generateUserKey(req, 'adaptive');
         const result = await limiter.isAllowed(userKey);

         res.set('X-RateLimit-Adaptive', 'true');
         res.set('X-RateLimit-System-Load', systemLoad.toString());
         
         if (!result.allowed) {
           return res.status(429).json({
             error: 'Rate limit exceeded (adaptive)',
             systemLoad: systemLoad,
             retryAfter: 60
           });
         }

         next();
       };
     }

     async getSystemLoad() {
       // Get system metrics (CPU, memory, etc.)
       const os = require('os');
       const loadAvg = os.loadavg()[0]; // 1-minute load average
       const cpuCount = os.cpus().length;
       return Math.min(1, loadAvg / cpuCount);
     }
   }

   module.exports = AdvancedRateLimiter;
   ```

5. **API Quota Management**
   - Implement comprehensive quota systems:

   **Quota Management System:**
   ```javascript
   // services/quota-manager.js
   class QuotaManager {
     constructor(redis, database) {
       this.redis = redis;
       this.database = database;
       this.quotaTypes = {
         'api_calls': { resetPeriod: 'monthly', defaultLimit: 10000 },
         'data_transfer': { resetPeriod: 'monthly', defaultLimit: 1073741824 }, // 1GB in bytes
         'storage': { resetPeriod: 'none', defaultLimit: 5368709120 }, // 5GB
         'concurrent_requests': { resetPeriod: 'none', defaultLimit: 10 }
       };
     }

     async checkQuota(userId, quotaType, amount = 1) {
       const userQuota = await this.getUserQuota(userId, quotaType);
       const currentUsage = await this.getCurrentUsage(userId, quotaType);

       const available = userQuota.limit - currentUsage;
       const allowed = available >= amount;

       if (allowed) {
         await this.incrementUsage(userId, quotaType, amount);
       }

       return {
         allowed,
         usage: currentUsage + (allowed ? amount : 0),
         limit: userQuota.limit,
         remaining: Math.max(0, available - (allowed ? amount : 0)),
         resetDate: userQuota.resetDate
       };
     }

     async getUserQuota(userId, quotaType) {
       // Get user-specific quota from database
       const customQuota = await this.database.query(
         'SELECT * FROM user_quotas WHERE user_id = $1 AND quota_type = $2',
         [userId, quotaType]
       );

       if (customQuota.rows.length > 0) {
         return customQuota.rows[0];
       }

       // Get plan-based quota
       const user = await this.database.query(
         'SELECT plan FROM users WHERE id = $1',
         [userId]
       );

       const planQuota = await this.getPlanQuota(user.rows[0]?.plan || 'free', quotaType);
       return planQuota;
     }

     async getPlanQuota(plan, quotaType) {
       const planQuotas = {
         free: {
           api_calls: 1000,
           data_transfer: 104857600, // 100MB
           storage: 1073741824, // 1GB
           concurrent_requests: 5
         },
         basic: {
           api_calls: 10000,
           data_transfer: 1073741824, // 1GB
           storage: 10737418240, // 10GB
           concurrent_requests: 10
         },
         pro: {
           api_calls: 100000,
           data_transfer: 10737418240, // 10GB
           storage: 107374182400, // 100GB
           concurrent_requests: 50
         },
         enterprise: {
           api_calls: 1000000,
           data_transfer: 107374182400, // 100GB
           storage: 1099511627776, // 1TB
           concurrent_requests: 200
         }
       };

       const limit = planQuotas[plan]?.[quotaType] || this.quotaTypes[quotaType].defaultLimit;
       const resetDate = this.calculateResetDate(quotaType);

       return { limit, resetDate };
     }

     async getCurrentUsage(userId, quotaType) {
       const quotaConfig = this.quotaTypes[quotaType];
       
       if (quotaConfig.resetPeriod === 'none') {
         // Non-resetting quota (like storage)
         const key = `quota:${userId}:${quotaType}:current`;
         const usage = await this.redis.get(key);
         return parseInt(usage) || 0;
       } else {
         // Resetting quota (like monthly API calls)
         const period = this.getCurrentPeriod(quotaConfig.resetPeriod);
         const key = `quota:${userId}:${quotaType}:${period}`;
         const usage = await this.redis.get(key);
         return parseInt(usage) || 0;
       }
     }

     async incrementUsage(userId, quotaType, amount) {
       const quotaConfig = this.quotaTypes[quotaType];
       
       if (quotaConfig.resetPeriod === 'none') {
         const key = `quota:${userId}:${quotaType}:current`;
         await this.redis.incrby(key, amount);
         await this.redis.expire(key, 86400 * 365); // 1 year TTL
       } else {
         const period = this.getCurrentPeriod(quotaConfig.resetPeriod);
         const key = `quota:${userId}:${quotaType}:${period}`;
         await this.redis.incrby(key, amount);
         
         // Set TTL to end of period
         const ttl = this.getTTLForPeriod(quotaConfig.resetPeriod);
         await this.redis.expire(key, ttl);
       }

       // Update usage analytics
       await this.recordUsageAnalytics(userId, quotaType, amount);
     }

     getCurrentPeriod(resetPeriod) {
       const now = new Date();
       
       switch (resetPeriod) {
         case 'daily':
           return now.toISOString().split('T')[0]; // YYYY-MM-DD
         case 'weekly':
           const weekStart = new Date(now);
           weekStart.setDate(now.getDate() - now.getDay());
           return weekStart.toISOString().split('T')[0];
         case 'monthly':
           return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
         case 'yearly':
           return now.getFullYear().toString();
         default:
           return 'current';
       }
     }

     calculateResetDate(quotaType) {
       const config = this.quotaTypes[quotaType];
       if (config.resetPeriod === 'none') return null;

       const now = new Date();
       const resetDate = new Date();

       switch (config.resetPeriod) {
         case 'daily':
           resetDate.setDate(now.getDate() + 1);
           resetDate.setHours(0, 0, 0, 0);
           break;
         case 'weekly':
           resetDate.setDate(now.getDate() + (7 - now.getDay()));
           resetDate.setHours(0, 0, 0, 0);
           break;
         case 'monthly':
           resetDate.setMonth(now.getMonth() + 1, 1);
           resetDate.setHours(0, 0, 0, 0);
           break;
         case 'yearly':
           resetDate.setFullYear(now.getFullYear() + 1, 0, 1);
           resetDate.setHours(0, 0, 0, 0);
           break;
       }

       return resetDate;
     }

     getTTLForPeriod(resetPeriod) {
       const resetDate = this.calculateResetDate({ resetPeriod });
       return Math.ceil((resetDate.getTime() - Date.now()) / 1000);
     }

     async recordUsageAnalytics(userId, quotaType, amount) {
       // Record usage for analytics and billing
       const analyticsKey = `analytics:usage:${userId}:${quotaType}:${new Date().toISOString().split('T')[0]}`;
       await this.redis.incrby(analyticsKey, amount);
       await this.redis.expire(analyticsKey, 86400 * 90); // 90 days retention
     }

     // Middleware for quota checking
     createQuotaMiddleware(quotaType, amountFn = () => 1) {
       return async (req, res, next) => {
         if (!req.user) {
           return next(); // Skip quota check for unauthenticated requests
         }

         const amount = typeof amountFn === 'function' ? amountFn(req) : amountFn;
         const result = await this.checkQuota(req.user.id, quotaType, amount);

         // Set quota headers
         res.set('X-Quota-Type', quotaType);
         res.set('X-Quota-Limit', result.limit.toString());
         res.set('X-Quota-Remaining', result.remaining.toString());
         res.set('X-Quota-Used', result.usage.toString());
         
         if (result.resetDate) {
           res.set('X-Quota-Reset', result.resetDate.toISOString());
         }

         if (!result.allowed) {
           return res.status(429).json({
             error: 'Quota exceeded',
             quotaType: quotaType,
             limit: result.limit,
             usage: result.usage,
             resetDate: result.resetDate
           });
         }

         req.quota = result;
         next();
       };
     }
   }

   module.exports = QuotaManager;
   ```

6. **Rate Limiting for Different Services**
   - Implement service-specific rate limiting:

   **Database Rate Limiting:**
   ```javascript
   // rate-limiters/database-rate-limiter.js
   class DatabaseRateLimiter {
     constructor(redis, pool) {
       this.redis = redis;
       this.pool = pool;
       this.connectionLimiter = new Map();
       this.queryLimiter = new Map();
     }

     // Limit concurrent database connections per user
     async acquireConnection(userId) {
       const key = `db:connections:${userId}`;
       const maxConnections = await this.getMaxConnections(userId);
       
       const script = `
         local key = KEYS[1]
         local maxConnections = tonumber(ARGV[1])
         local ttl = tonumber(ARGV[2])
         
         local current = redis.call('GET', key) or 0
         current = tonumber(current)
         
         if current < maxConnections then
           redis.call('INCR', key)
           redis.call('EXPIRE', key, ttl)
           return 1
         else
           return 0
         end
       `;

       const allowed = await this.redis.eval(script, 1, key, maxConnections, 300); // 5 min TTL
       
       if (!allowed) {
         throw new Error('Database connection limit exceeded');
       }

       return {
         release: async () => {
           await this.redis.decr(key);
         }
       };
     }

     // Rate limit expensive queries
     async checkQueryLimit(userId, queryType, cost = 1) {
       const key = `db:queries:${userId}:${queryType}`;
       const windowMs = 60000; // 1 minute
       const maxCost = await this.getMaxQueryCost(userId, queryType);

       const script = `
         local key = KEYS[1]
         local windowMs = tonumber(ARGV[1])
         local maxCost = tonumber(ARGV[2])
         local cost = tonumber(ARGV[3])
         local now = tonumber(ARGV[4])
         
         local windowStart = now - windowMs
         
         -- Remove old entries
         redis.call('ZREMRANGEBYSCORE', key, 0, windowStart)
         
         -- Get current cost
         local currentCost = 0
         local entries = redis.call('ZRANGE', key, 0, -1, 'WITHSCORES')
         for i = 2, #entries, 2 do
           currentCost = currentCost + tonumber(entries[i])
         end
         
         if currentCost + cost <= maxCost then
           redis.call('ZADD', key, cost, now)
           redis.call('EXPIRE', key, math.ceil(windowMs / 1000))
           return {1, currentCost + cost, maxCost - currentCost - cost}
         else
           return {0, currentCost, maxCost - currentCost}
         end
       `;

       const result = await this.redis.eval(
         script, 1, key, windowMs, maxCost, cost, Date.now()
       );

       return {
         allowed: result[0] === 1,
         currentCost: result[1],
         remaining: result[2]
       };
     }

     async getMaxConnections(userId) {
       // Get from user plan or use default
       const user = await this.getUserPlan(userId);
       const connectionLimits = {
         free: 2,
         basic: 5,
         pro: 20,
         enterprise: 100
       };
       return connectionLimits[user.plan] || 2;
     }

     async getMaxQueryCost(userId, queryType) {
       const user = await this.getUserPlan(userId);
       const costLimits = {
         free: { select: 100, insert: 50, update: 30, delete: 10 },
         basic: { select: 500, insert: 200, update: 100, delete: 50 },
         pro: { select: 2000, insert: 1000, update: 500, delete: 200 },
         enterprise: { select: 10000, insert: 5000, update: 2500, delete: 1000 }
       };
       return costLimits[user.plan]?.[queryType] || 10;
     }
   }
   ```

   **File Upload Rate Limiting:**
   ```javascript
   // rate-limiters/upload-rate-limiter.js
   class UploadRateLimiter {
     constructor(redis) {
       this.redis = redis;
     }

     // Limit file upload size and frequency
     async checkUploadLimit(userId, fileSize, fileType) {
       const checks = await Promise.all([
         this.checkFileSizeLimit(userId, fileSize),
         this.checkUploadFrequency(userId),
         this.checkStorageQuota(userId, fileSize),
         this.checkFileTypeLimit(userId, fileType)
       ]);

       const failed = checks.find(check => !check.allowed);
       if (failed) {
         return failed;
       }

       // Record the upload
       await this.recordUpload(userId, fileSize, fileType);

       return { allowed: true, checks };
     }

     async checkFileSizeLimit(userId, fileSize) {
       const user = await this.getUserPlan(userId);
       const sizeLimits = {
         free: 10 * 1024 * 1024,      // 10MB
         basic: 50 * 1024 * 1024,     // 50MB
         pro: 200 * 1024 * 1024,      // 200MB
         enterprise: 1000 * 1024 * 1024 // 1GB
       };

       const maxSize = sizeLimits[user.plan] || sizeLimits.free;
       const allowed = fileSize <= maxSize;

       return {
         allowed,
         type: 'file_size',
         current: fileSize,
         limit: maxSize,
         message: allowed ? null : `File size ${fileSize} exceeds limit of ${maxSize} bytes`
       };
     }

     async checkUploadFrequency(userId) {
       const key = `uploads:frequency:${userId}`;
       const windowMs = 60000; // 1 minute
       const maxUploads = await this.getMaxUploadsPerMinute(userId);

       const current = await this.redis.incr(key);
       if (current === 1) {
         await this.redis.expire(key, Math.ceil(windowMs / 1000));
       }

       return {
         allowed: current <= maxUploads,
         type: 'upload_frequency',
         current,
         limit: maxUploads,
         window: windowMs
       };
     }

     async checkStorageQuota(userId, fileSize) {
       const key = `storage:used:${userId}`;
       const currentUsage = parseInt(await this.redis.get(key)) || 0;
       const maxStorage = await this.getMaxStorage(userId);

       const allowed = (currentUsage + fileSize) <= maxStorage;

       return {
         allowed,
         type: 'storage_quota',
         current: currentUsage + fileSize,
         limit: maxStorage,
         fileSize
       };
     }

     async checkFileTypeLimit(userId, fileType) {
       const allowedTypes = await this.getAllowedFileTypes(userId);
       const allowed = allowedTypes.includes(fileType);

       return {
         allowed,
         type: 'file_type',
         fileType,
         allowedTypes,
         message: allowed ? null : `File type ${fileType} not allowed`
       };
     }

     async recordUpload(userId, fileSize, fileType) {
       const now = Date.now();
       
       // Update storage usage
       await this.redis.incrby(`storage:used:${userId}`, fileSize);
       
       // Record upload in analytics
       const analyticsKey = `analytics:uploads:${userId}:${new Date().toISOString().split('T')[0]}`;
       await this.redis.hincrby(analyticsKey, 'count', 1);
       await this.redis.hincrby(analyticsKey, 'bytes', fileSize);
       await this.redis.expire(analyticsKey, 86400 * 30); // 30 days
     }

     createUploadMiddleware() {
       return async (req, res, next) => {
         if (!req.user) {
           return res.status(401).json({ error: 'Authentication required' });
         }

         // Check if this is a file upload
         if (!req.files || !req.files.length) {
           return next();
         }

         for (const file of req.files) {
           const result = await this.checkUploadLimit(
             req.user.id,
             file.size,
             file.mimetype
           );

           if (!result.allowed) {
             return res.status(429).json({
               error: 'Upload limit exceeded',
               ...result
             });
           }
         }

         next();
       };
     }
   }
   ```

7. **Rate Limiting Dashboard and Analytics**
   - Monitor and analyze rate limiting effectiveness:

   **Rate Limiting Analytics:**
   ```javascript
   // analytics/rate-limit-analytics.js
   class RateLimitAnalytics {
     constructor(redis, database) {
       this.redis = redis;
       this.database = database;
     }

     async recordRateLimitHit(userId, endpoint, limitType, blocked) {
       const timestamp = Date.now();
       const date = new Date().toISOString().split('T')[0];

       // Real-time metrics
       const realtimeKey = `analytics:ratelimit:realtime:${limitType}`;
       await this.redis.zadd(realtimeKey, timestamp, `${userId}:${endpoint}:${blocked}`);
       await this.redis.expire(realtimeKey, 3600); // 1 hour

       // Daily aggregates
       const dailyKey = `analytics:ratelimit:daily:${date}:${limitType}`;
       await this.redis.hincrby(dailyKey, 'total', 1);
       if (blocked) {
         await this.redis.hincrby(dailyKey, 'blocked', 1);
       }
       await this.redis.expire(dailyKey, 86400 * 30); // 30 days

       // User-specific analytics
       const userKey = `analytics:ratelimit:user:${userId}:${date}`;
       await this.redis.hincrby(userKey, endpoint, 1);
       if (blocked) {
         await this.redis.hincrby(userKey, `${endpoint}:blocked`, 1);
       }
       await this.redis.expire(userKey, 86400 * 30);
     }

     async getRateLimitStats(timeRange = '24h') {
       const now = Date.now();
       const ranges = {
         '1h': 3600000,
         '24h': 86400000,
         '7d': 604800000,
         '30d': 2592000000
       };

       const rangeMs = ranges[timeRange] || ranges['24h'];
       const startTime = now - rangeMs;

       // Get realtime data for shorter ranges
       if (rangeMs <= 3600000) {
         return await this.getRealtimeStats(startTime, now);
       }

       // Get aggregated data for longer ranges
       return await this.getAggregatedStats(startTime, now);
     }

     async getRealtimeStats(startTime, endTime) {
       const limitTypes = ['general', 'auth', 'upload', 'api'];
       const stats = {};

       for (const limitType of limitTypes) {
         const key = `analytics:ratelimit:realtime:${limitType}`;
         const entries = await this.redis.zrangebyscore(key, startTime, endTime);
         
         let total = 0;
         let blocked = 0;
         const endpoints = {};

         for (const entry of entries) {
           const [userId, endpoint, isBlocked] = entry.split(':');
           total++;
           if (isBlocked === 'true') blocked++;

           if (!endpoints[endpoint]) {
             endpoints[endpoint] = { total: 0, blocked: 0 };
           }
           endpoints[endpoint].total++;
           if (isBlocked === 'true') endpoints[endpoint].blocked++;
         }

         stats[limitType] = {
           total,
           blocked,
           allowed: total - blocked,
           blockRate: total > 0 ? (blocked / total) : 0,
           endpoints
         };
       }

       return stats;
     }

     async getTopBlockedEndpoints(timeRange = '24h', limit = 10) {
       const stats = await this.getRateLimitStats(timeRange);
       const endpointStats = [];

       for (const [limitType, data] of Object.entries(stats)) {
         for (const [endpoint, endpointData] of Object.entries(data.endpoints || {})) {
           endpointStats.push({
             endpoint,
             limitType,
             ...endpointData,
             blockRate: endpointData.total > 0 ? (endpointData.blocked / endpointData.total) : 0
           });
         }
       }

       return endpointStats
         .sort((a, b) => b.blocked - a.blocked)
         .slice(0, limit);
     }

     async getUserRateLimitStats(userId, timeRange = '7d') {
       const now = new Date();
       const days = parseInt(timeRange.replace('d', ''));
       const stats = [];

       for (let i = 0; i < days; i++) {
         const date = new Date(now - i * 86400000).toISOString().split('T')[0];
         const key = `analytics:ratelimit:user:${userId}:${date}`;
         const dayStats = await this.redis.hgetall(key);
         
         const endpoints = {};
         for (const [field, value] of Object.entries(dayStats)) {
           if (field.endsWith(':blocked')) {
             const endpoint = field.replace(':blocked', '');
             if (!endpoints[endpoint]) endpoints[endpoint] = { total: 0, blocked: 0 };
             endpoints[endpoint].blocked = parseInt(value);
           } else {
             if (!endpoints[field]) endpoints[field] = { total: 0, blocked: 0 };
             endpoints[field].total = parseInt(value);
           }
         }

         stats.push({ date, endpoints });
       }

       return stats;
     }

     async generateRateLimitReport() {
       const report = {
         generatedAt: new Date().toISOString(),
         summary: await this.getRateLimitStats('24h'),
         topBlockedEndpoints: await this.getTopBlockedEndpoints('24h'),
         trends: await this.getRateLimitTrends(),
         recommendations: await this.generateRecommendations()
       };

       return report;
     }

     async generateRecommendations() {
       const stats = await this.getRateLimitStats('24h');
       const recommendations = [];

       for (const [limitType, data] of Object.entries(stats)) {
         if (data.blockRate > 0.1) { // >10% block rate
           recommendations.push({
             severity: 'high',
             type: 'high_block_rate',
             limitType,
             blockRate: data.blockRate,
             message: `High block rate (${(data.blockRate * 100).toFixed(1)}%) for ${limitType} rate limiter`,
             suggestions: [
               'Consider increasing rate limits for legitimate users',
               'Implement user-specific rate limiting',
               'Add rate limit exemptions for trusted IPs'
             ]
           });
         }

         if (data.total > 100000) { // High volume
           recommendations.push({
             severity: 'medium',
             type: 'high_volume',
             limitType,
             volume: data.total,
             message: `High request volume (${data.total}) detected for ${limitType}`,
             suggestions: [
               'Monitor for potential abuse patterns',
               'Consider implementing adaptive rate limiting',
               'Review capacity planning'
             ]
           });
         }
       }

       return recommendations;
     }
   }

   module.exports = RateLimitAnalytics;
   ```

8. **Rate Limiting Configuration Management**
   - Dynamic rate limit configuration:

   **Configuration Manager:**
   ```javascript
   // config/rate-limit-config.js
   class RateLimitConfigManager {
     constructor(redis, database) {
       this.redis = redis;
       this.database = database;
       this.configCache = new Map();
       this.setupDefaultConfigs();
     }

     setupDefaultConfigs() {
       this.defaultConfigs = {
         'api:general': {
           windowMs: 900000, // 15 minutes
           max: 1000,
           algorithm: 'sliding-window',
           skipSuccessfulRequests: false,
           enabled: true
         },
         'api:auth': {
           windowMs: 900000, // 15 minutes
           max: 5,
           algorithm: 'token-bucket',
           skipSuccessfulRequests: true,
           enabled: true
         },
         'api:upload': {
           capacity: 10,
           refillRate: 1,
           refillPeriod: 10000,
           algorithm: 'token-bucket',
           enabled: true
         },
         'api:search': {
           windowMs: 60000, // 1 minute
           max: 100,
           algorithm: 'sliding-window',
           enabled: true
         }
       };
     }

     async getConfig(limiterId) {
       // Check cache first
       if (this.configCache.has(limiterId)) {
         const cached = this.configCache.get(limiterId);
         if (Date.now() - cached.timestamp < 300000) { // 5 min cache
           return cached.config;
         }
       }

       // Get from database
       let config = await this.database.query(
         'SELECT * FROM rate_limit_configs WHERE limiter_id = $1',
         [limiterId]
       );

       if (config.rows.length === 0) {
         // Use default config
         config = this.defaultConfigs[limiterId] || this.defaultConfigs['api:general'];
       } else {
         config = config.rows[0].config;
       }

       // Cache the config
       this.configCache.set(limiterId, {
         config,
         timestamp: Date.now()
       });

       return config;
     }

     async updateConfig(limiterId, newConfig, userId) {
       // Validate config
       const validationResult = this.validateConfig(newConfig);
       if (!validationResult.valid) {
         throw new Error(`Invalid config: ${validationResult.errors.join(', ')}`);
       }

       // Save to database
       await this.database.query(`
         INSERT INTO rate_limit_configs (limiter_id, config, updated_by, updated_at)
         VALUES ($1, $2, $3, NOW())
         ON CONFLICT (limiter_id) 
         DO UPDATE SET config = $2, updated_by = $3, updated_at = NOW()
       `, [limiterId, JSON.stringify(newConfig), userId]);

       // Clear cache
       this.configCache.delete(limiterId);

       // Notify other instances of config change
       await this.redis.publish('rate-limit-config-update', JSON.stringify({
         limiterId,
         config: newConfig,
         updatedBy: userId,
         timestamp: Date.now()
       }));

       return newConfig;
     }

     validateConfig(config) {
       const errors = [];

       if (config.algorithm === 'sliding-window') {
         if (!config.windowMs || config.windowMs < 1000) {
           errors.push('windowMs must be at least 1000ms');
         }
         if (!config.max || config.max < 1) {
           errors.push('max must be at least 1');
         }
       } else if (config.algorithm === 'token-bucket') {
         if (!config.capacity || config.capacity < 1) {
           errors.push('capacity must be at least 1');
         }
         if (!config.refillRate || config.refillRate < 1) {
           errors.push('refillRate must be at least 1');
         }
         if (!config.refillPeriod || config.refillPeriod < 1000) {
           errors.push('refillPeriod must be at least 1000ms');
         }
       } else {
         errors.push('algorithm must be either sliding-window or token-bucket');
       }

       return {
         valid: errors.length === 0,
         errors
       };
     }

     // A/B testing for rate limit configurations
     async createABTest(limiterId, configA, configB, trafficSplit = 0.5) {
       const testId = `ab-test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
       
       await this.database.query(`
         INSERT INTO rate_limit_ab_tests 
         (test_id, limiter_id, config_a, config_b, traffic_split, created_at, status)
         VALUES ($1, $2, $3, $4, $5, NOW(), 'active')
       `, [testId, limiterId, JSON.stringify(configA), JSON.stringify(configB), trafficSplit]);

       return testId;
     }

     async getABTestConfig(limiterId, userKey) {
       const activeTest = await this.database.query(`
         SELECT * FROM rate_limit_ab_tests 
         WHERE limiter_id = $1 AND status = 'active'
         ORDER BY created_at DESC LIMIT 1
       `, [limiterId]);

       if (activeTest.rows.length === 0) {
         return await this.getConfig(limiterId);
       }

       const test = activeTest.rows[0];
       const hash = this.hashString(userKey);
       const bucket = (hash % 100) / 100;

       if (bucket < test.traffic_split) {
         return test.config_a;
       } else {
         return test.config_b;
       }
     }

     hashString(str) {
       let hash = 0;
       for (let i = 0; i < str.length; i++) {
         const char = str.charCodeAt(i);
         hash = ((hash << 5) - hash) + char;
         hash = hash & hash; // Convert to 32-bit integer
       }
       return Math.abs(hash);
     }

     // Admin dashboard endpoints
     async getAllConfigs() {
       const configs = await this.database.query(`
         SELECT limiter_id, config, updated_by, updated_at 
         FROM rate_limit_configs 
         ORDER BY updated_at DESC
       `);

       return configs.rows.map(row => ({
         limiterId: row.limiter_id,
         config: row.config,
         updatedBy: row.updated_by,
         updatedAt: row.updated_at
       }));
     }

     async getConfigHistory(limiterId) {
       const history = await this.database.query(`
         SELECT config, updated_by, updated_at 
         FROM rate_limit_config_history 
         WHERE limiter_id = $1 
         ORDER BY updated_at DESC 
         LIMIT 50
       `, [limiterId]);

       return history.rows;
     }
   }

   module.exports = RateLimitConfigManager;
   ```

9. **Testing Rate Limits**
   - Comprehensive rate limiting tests:

   **Rate Limiting Test Suite:**
   ```javascript
   // tests/rate-limiting.test.js
   const request = require('supertest');
   const app = require('../app');
   const Redis = require('ioredis');

   describe('Rate Limiting', () => {
     let redis;

     beforeAll(async () => {
       redis = new Redis(process.env.REDIS_TEST_URL);
     });

     afterEach(async () => {
       // Clean up rate limiting keys
       const keys = await redis.keys('*rate*');
       if (keys.length > 0) {
         await redis.del(...keys);
       }
     });

     afterAll(async () => {
       await redis.disconnect();
     });

     describe('General API Rate Limiting', () => {
       test('should allow requests within limit', async () => {
         for (let i = 0; i < 5; i++) {
           const response = await request(app)
             .get('/api/test')
             .expect(200);

           expect(response.headers).toHaveProperty('x-ratelimit-remaining');
           expect(parseInt(response.headers['x-ratelimit-remaining'])).toBeGreaterThan(0);
         }
       });

       test('should block requests exceeding limit', async () => {
         // Make requests up to the limit
         const limit = 10; // Assuming limit is 10 for test endpoint
         
         for (let i = 0; i < limit; i++) {
           await request(app).get('/api/test').expect(200);
         }

         // Next request should be rate limited
         const response = await request(app)
           .get('/api/test')
           .expect(429);

         expect(response.body).toHaveProperty('error');
         expect(response.body.error).toContain('Rate limit exceeded');
       });

       test('should include proper rate limit headers', async () => {
         const response = await request(app)
           .get('/api/test')
           .expect(200);

         expect(response.headers).toHaveProperty('x-ratelimit-limit');
         expect(response.headers).toHaveProperty('x-ratelimit-remaining');
         expect(response.headers).toHaveProperty('x-ratelimit-window');
       });

       test('should reset rate limit after window expires', async () => {
         // Use a short window for testing
         const shortWindowApp = createTestAppWithShortWindow(1000); // 1 second

         // Exhaust the limit
         await request(shortWindowApp).get('/api/test').expect(200);
         await request(shortWindowApp).get('/api/test').expect(429);

         // Wait for window to reset
         await new Promise(resolve => setTimeout(resolve, 1100));

         // Should allow requests again
         await request(shortWindowApp).get('/api/test').expect(200);
       });
     });

     describe('Authentication Rate Limiting', () => {
       test('should limit failed login attempts', async () => {
         const loginData = { email: 'test@example.com', password: 'wrongpassword' };

         // Make several failed attempts
         for (let i = 0; i < 5; i++) {
           await request(app)
             .post('/api/auth/login')
             .send(loginData)
             .expect(401);
         }

         // Next attempt should be rate limited
         const response = await request(app)
           .post('/api/auth/login')
           .send(loginData)
           .expect(429);

         expect(response.body.error).toContain('Too many authentication attempts');
       });

       test('should not count successful logins against rate limit', async () => {
         const loginData = { email: 'test@example.com', password: 'correctpassword' };

         // Make successful login attempts
         for (let i = 0; i < 3; i++) {
           await request(app)
             .post('/api/auth/login')
             .send(loginData)
             .expect(200);
         }

         // Should still allow more attempts
         await request(app)
           .post('/api/auth/login')
           .send(loginData)
           .expect(200);
       });
     });

     describe('User-Specific Rate Limiting', () => {
       test('should apply different limits based on user tier', async () => {
         const freeUserToken = await getTestToken('free');
         const proUserToken = await getTestToken('pro');

         // Free user should have lower limits
         const freeUserLimit = await findRateLimit(app, '/api/data', freeUserToken);
         
         // Pro user should have higher limits
         const proUserLimit = await findRateLimit(app, '/api/data', proUserToken);

         expect(proUserLimit).toBeGreaterThan(freeUserLimit);
       });

       test('should rate limit by user ID when authenticated', async () => {
         const userToken = await getTestToken();
         
         // Make requests with user token
         for (let i = 0; i < 10; i++) {
           await request(app)
             .get('/api/user/profile')
             .set('Authorization', `Bearer ${userToken}`)
             .expect(200);
         }

         // Should be rate limited
         await request(app)
           .get('/api/user/profile')
           .set('Authorization', `Bearer ${userToken}`)
           .expect(429);
       });
     });

     describe('Quota Management', () => {
       test('should enforce API call quotas', async () => {
         const userToken = await getTestToken('basic'); // Basic plan has limited quota
         
         // Make requests up to quota limit
         const quota = await getUserQuota('basic', 'api_calls');
         
         for (let i = 0; i < quota; i++) {
           await request(app)
             .get('/api/data')
             .set('Authorization', `Bearer ${userToken}`)
             .expect(200);
         }

         // Next request should exceed quota
         const response = await request(app)
           .get('/api/data')
           .set('Authorization', `Bearer ${userToken}`)
           .expect(429);

         expect(response.body.error).toContain('Quota exceeded');
         expect(response.body).toHaveProperty('quotaType', 'api_calls');
       });

       test('should include quota headers in responses', async () => {
         const userToken = await getTestToken();
         
         const response = await request(app)
           .get('/api/data')
           .set('Authorization', `Bearer ${userToken}`)
           .expect(200);

         expect(response.headers).toHaveProperty('x-quota-limit');
         expect(response.headers).toHaveProperty('x-quota-remaining');
         expect(response.headers).toHaveProperty('x-quota-used');
       });
     });

     describe('Rate Limiting Bypass', () => {
       test('should bypass rate limits for internal requests', async () => {
         // Make many requests with internal header
         for (let i = 0; i < 100; i++) {
           await request(app)
             .get('/api/test')
             .set('X-Internal-Request', 'true')
             .expect(200);
         }

         // All should succeed
       });

       test('should bypass rate limits for whitelisted IPs', async () => {
         // Configure test to use whitelisted IP
         // This would depend on your specific implementation
       });
     });

     // Helper functions
     async function findRateLimit(app, endpoint, token) {
       let requests = 0;
       
       while (requests < 1000) { // Safety limit
         const response = await request(app)
           .get(endpoint)
           .set('Authorization', `Bearer ${token}`);
         
         requests++;
         
         if (response.status === 429) {
           return requests - 1;
         }
       }
       
       return requests;
     }

     async function getTestToken(tier = 'free') {
       // Implementation depends on your auth system
       return 'test-token';
     }

     async function getUserQuota(plan, quotaType) {
       const quotas = {
         free: { api_calls: 100 },
         basic: { api_calls: 1000 },
         pro: { api_calls: 10000 }
       };
       return quotas[plan][quotaType];
     }

     function createTestAppWithShortWindow(windowMs) {
       // Create a test app instance with short rate limit window
       // Implementation depends on your app structure
       return app;
     }
   });
   ```

10. **Production Monitoring and Alerting**
    - Monitor rate limiting effectiveness:

    **Rate Limiting Monitoring:**
    ```javascript
    // monitoring/rate-limit-monitor.js
    class RateLimitMonitor {
      constructor(redis, alertService) {
        this.redis = redis;
        this.alertService = alertService;
        this.thresholds = {
          highBlockRate: 0.15, // 15%
          highVolume: 10000,    // requests per minute
          quotaExhaustion: 0.9  // 90% quota usage
        };
      }

      async startMonitoring(interval = 60000) {
        setInterval(async () => {
          await this.checkRateLimitHealth();
        }, interval);
      }

      async checkRateLimitHealth() {
        const metrics = await this.collectMetrics();
        const alerts = [];

        // Check for high block rates
        for (const [limitType, data] of Object.entries(metrics)) {
          if (data.blockRate > this.thresholds.highBlockRate) {
            alerts.push({
              type: 'high_block_rate',
              limitType,
              blockRate: data.blockRate,
              message: `High block rate (${(data.blockRate * 100).toFixed(1)}%) for ${limitType}`,
              severity: 'warning'
            });
          }

          if (data.requestsPerMinute > this.thresholds.highVolume) {
            alerts.push({
              type: 'high_volume',
              limitType,
              volume: data.requestsPerMinute,
              message: `High request volume (${data.requestsPerMinute}/min) for ${limitType}`,
              severity: 'info'
            });
          }
        }

        // Check for quota exhaustion patterns
        const quotaAlerts = await this.checkQuotaExhaustion();
        alerts.push(...quotaAlerts);

        // Send alerts
        for (const alert of alerts) {
          await this.alertService.sendAlert(alert);
        }

        // Store metrics for historical analysis
        await this.storeMetrics(metrics);
      }

      async collectMetrics() {
        const limitTypes = ['general', 'auth', 'upload', 'api'];
        const metrics = {};
        const now = Date.now();
        const minuteAgo = now - 60000;

        for (const limitType of limitTypes) {
          const key = `analytics:ratelimit:realtime:${limitType}`;
          const entries = await this.redis.zrangebyscore(key, minuteAgo, now);
          
          let total = 0;
          let blocked = 0;

          for (const entry of entries) {
            const [userId, endpoint, isBlocked] = entry.split(':');
            total++;
            if (isBlocked === 'true') blocked++;
          }

          metrics[limitType] = {
            total,
            blocked,
            allowed: total - blocked,
            blockRate: total > 0 ? (blocked / total) : 0,
            requestsPerMinute: total
          };
        }

        return metrics;
      }

      async checkQuotaExhaustion() {
        const alerts = [];
        const quotaKeys = await this.redis.keys('quota:*:current');

        for (const key of quotaKeys.slice(0, 100)) { // Limit to prevent overload
          const [, userId, quotaType] = key.split(':');
          const usage = parseInt(await this.redis.get(key)) || 0;
          
          // Get user's quota limit
          const limit = await this.getUserQuotaLimit(userId, quotaType);
          const usageRate = usage / limit;

          if (usageRate > this.thresholds.quotaExhaustion) {
            alerts.push({
              type: 'quota_exhaustion',
              userId,
              quotaType,
              usage,
              limit,
              usageRate,
              message: `User ${userId} has used ${(usageRate * 100).toFixed(1)}% of ${quotaType} quota`,
              severity: 'warning'
            });
          }
        }

        return alerts;
      }

      async storeMetrics(metrics) {
        const timestamp = Date.now();
        const metricsKey = `metrics:ratelimit:${timestamp}`;
        
        await this.redis.hmset(metricsKey, 
          'timestamp', timestamp,
          'metrics', JSON.stringify(metrics)
        );
        await this.redis.expire(metricsKey, 86400 * 7); // 7 days retention
      }

      async generateHealthReport() {
        const endTime = Date.now();
        const startTime = endTime - 86400000; // 24 hours
        
        const metricKeys = await this.redis.keys('metrics:ratelimit:*');
        const recentKeys = metricKeys.filter(key => {
          const timestamp = parseInt(key.split(':')[2]);
          return timestamp >= startTime && timestamp <= endTime;
        });

        const metrics = [];
        for (const key of recentKeys) {
          const data = await this.redis.hgetall(key);
          metrics.push({
            timestamp: parseInt(data.timestamp),
            metrics: JSON.parse(data.metrics)
          });
        }

        return {
          period: { start: startTime, end: endTime },
          dataPoints: metrics.length,
          summary: this.calculateSummaryStats(metrics),
          trends: this.calculateTrends(metrics),
          recommendations: this.generateRecommendations(metrics)
        };
      }

      calculateSummaryStats(metrics) {
        if (metrics.length === 0) return {};

        const summary = {};
        const limitTypes = ['general', 'auth', 'upload', 'api'];

        for (const limitType of limitTypes) {
          const values = metrics.map(m => m.metrics[limitType]).filter(Boolean);
          
          if (values.length > 0) {
            summary[limitType] = {
              avgBlockRate: values.reduce((sum, v) => sum + v.blockRate, 0) / values.length,
              avgVolume: values.reduce((sum, v) => sum + v.requestsPerMinute, 0) / values.length,
              maxVolume: Math.max(...values.map(v => v.requestsPerMinute)),
              totalRequests: values.reduce((sum, v) => sum + v.total, 0),
              totalBlocked: values.reduce((sum, v) => sum + v.blocked, 0)
            };
          }
        }

        return summary;
      }

      calculateTrends(metrics) {
        // Simple trend calculation - compare first and last hour
        if (metrics.length < 2) return {};

        const firstHour = metrics.slice(0, Math.min(60, metrics.length));
        const lastHour = metrics.slice(-Math.min(60, metrics.length));

        const trends = {};
        const limitTypes = ['general', 'auth', 'upload', 'api'];

        for (const limitType of limitTypes) {
          const firstAvg = this.calculateAverage(firstHour, limitType, 'requestsPerMinute');
          const lastAvg = this.calculateAverage(lastHour, limitType, 'requestsPerMinute');
          
          if (firstAvg > 0) {
            trends[limitType] = {
              volumeChange: ((lastAvg - firstAvg) / firstAvg) * 100,
              direction: lastAvg > firstAvg ? 'increasing' : 'decreasing'
            };
          }
        }

        return trends;
      }

      calculateAverage(metrics, limitType, field) {
        const values = metrics
          .map(m => m.metrics[limitType]?.[field])
          .filter(v => v !== undefined);
        
        return values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0;
      }

      generateRecommendations(metrics) {
        const recommendations = [];
        const summary = this.calculateSummaryStats(metrics);

        for (const [limitType, stats] of Object.entries(summary)) {
          if (stats.avgBlockRate > 0.1) {
            recommendations.push({
              priority: 'high',
              type: 'increase_limits',
              limitType,
              current: `${(stats.avgBlockRate * 100).toFixed(1)}% block rate`,
              suggestion: `Consider increasing rate limits for ${limitType} - high block rate indicates legitimate users may be affected`
            });
          }

          if (stats.avgVolume > 1000 && stats.avgBlockRate < 0.01) {
            recommendations.push({
              priority: 'medium',
              type: 'optimize_performance',
              limitType,
              current: `${stats.avgVolume.toFixed(0)} requests/min`,
              suggestion: `High volume with low block rate for ${limitType} - consider optimizing backend performance`
            });
          }
        }

        return recommendations;
      }
    }

    module.exports = RateLimitMonitor;
    ```