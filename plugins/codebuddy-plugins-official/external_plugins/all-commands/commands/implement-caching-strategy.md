---
description: Design and implement caching solutions
category: performance-optimization
---

# Implement Caching Strategy

Design and implement caching solutions

## Instructions

1. **Caching Strategy Analysis**
   - Analyze application architecture and identify caching opportunities
   - Assess current performance bottlenecks and data access patterns
   - Define caching requirements (TTL, invalidation, consistency)
   - Plan multi-layer caching architecture (browser, CDN, application, database)
   - Evaluate caching technologies and storage solutions

2. **Browser and Client-Side Caching**
   - Configure HTTP caching headers and cache policies:

   **HTTP Cache Headers:**
   ```javascript
   // Express.js middleware
   app.use((req, res, next) => {
     // Static assets with long-term caching
     if (req.url.match(/\.(js|css|png|jpg|jpeg|gif|ico|svg)$/)) {
       res.setHeader('Cache-Control', 'public, max-age=31536000'); // 1 year
       res.setHeader('ETag', generateETag(req.url));
     }
     
     // API responses with short-term caching
     if (req.url.startsWith('/api/')) {
       res.setHeader('Cache-Control', 'public, max-age=300'); // 5 minutes
     }
     
     next();
   });
   ```

   **Service Worker Caching:**
   ```javascript
   // sw.js - Service Worker
   const CACHE_NAME = 'app-cache-v1';
   const urlsToCache = [
     '/',
     '/static/js/bundle.js',
     '/static/css/main.css',
   ];

   self.addEventListener('install', (event) => {
     event.waitUntil(
       caches.open(CACHE_NAME)
         .then((cache) => cache.addAll(urlsToCache))
     );
   });

   self.addEventListener('fetch', (event) => {
     event.respondWith(
       caches.match(event.request)
         .then((response) => {
           // Return cached version or fetch from network
           return response || fetch(event.request);
         })
     );
   });
   ```

3. **Application-Level Caching**
   - Implement in-memory and distributed caching:

   **Node.js Memory Cache:**
   ```javascript
   const NodeCache = require('node-cache');
   const cache = new NodeCache({ stdTTL: 600 }); // 10 minutes default TTL

   class CacheService {
     static get(key) {
       return cache.get(key);
     }

     static set(key, value, ttl = 600) {
       return cache.set(key, value, ttl);
     }

     static del(key) {
       return cache.del(key);
     }

     static flush() {
       return cache.flushAll();
     }

     // Cache wrapper for expensive operations
     static async memoize(key, fn, ttl = 600) {
       let result = this.get(key);
       if (result === undefined) {
         result = await fn();
         this.set(key, result, ttl);
       }
       return result;
     }
   }

   // Usage example
   app.get('/api/users/:id', async (req, res) => {
     const userId = req.params.id;
     const cacheKey = `user:${userId}`;
     
     const user = await CacheService.memoize(
       cacheKey,
       () => getUserFromDatabase(userId),
       900 // 15 minutes
     );
     
     res.json(user);
   });
   ```

   **Redis Distributed Cache:**
   ```javascript
   const redis = require('redis');
   const client = redis.createClient({
     host: process.env.REDIS_HOST || 'localhost',
     port: process.env.REDIS_PORT || 6379,
   });

   class RedisCache {
     static async get(key) {
       try {
         const value = await client.get(key);
         return value ? JSON.parse(value) : null;
       } catch (error) {
         console.error('Cache get error:', error);
         return null;
       }
     }

     static async set(key, value, ttl = 600) {
       try {
         const serialized = JSON.stringify(value);
         if (ttl) {
           await client.setex(key, ttl, serialized);
         } else {
           await client.set(key, serialized);
         }
         return true;
       } catch (error) {
         console.error('Cache set error:', error);
         return false;
       }
     }

     static async del(key) {
       try {
         await client.del(key);
         return true;
       } catch (error) {
         console.error('Cache delete error:', error);
         return false;
       }
     }

     // Pattern-based cache invalidation
     static async invalidatePattern(pattern) {
       try {
         const keys = await client.keys(pattern);
         if (keys.length > 0) {
           await client.del(keys);
         }
         return true;
       } catch (error) {
         console.error('Cache invalidation error:', error);
         return false;
       }
     }
   }
   ```

4. **Database Query Caching**
   - Implement database-level caching strategies:

   **PostgreSQL Query Caching:**
   ```javascript
   const { Pool } = require('pg');
   const pool = new Pool();

   class DatabaseCache {
     static async cachedQuery(sql, params = [], ttl = 300) {
       const cacheKey = `query:${Buffer.from(sql + JSON.stringify(params)).toString('base64')}`;
       
       // Try cache first
       let result = await RedisCache.get(cacheKey);
       if (result) {
         return result;
       }
       
       // Execute query and cache result
       const dbResult = await pool.query(sql, params);
       result = dbResult.rows;
       
       await RedisCache.set(cacheKey, result, ttl);
       return result;
     }

     // Invalidate cache by table
     static async invalidateTable(tableName) {
       await RedisCache.invalidatePattern(`query:*${tableName}*`);
     }
   }

   // Usage
   app.get('/api/products', async (req, res) => {
     const products = await DatabaseCache.cachedQuery(
       'SELECT * FROM products WHERE active = true ORDER BY created_at DESC',
       [],
       600 // 10 minutes
     );
     res.json(products);
   });
   ```

   **MongoDB Caching with Mongoose:**
   ```javascript
   const mongoose = require('mongoose');

   // Mongoose query caching plugin
   function cachePlugin(schema) {
     schema.add({
       cacheKey: { type: String, index: true },
       cachedAt: { type: Date },
     });

     schema.methods.cache = function(ttl = 300) {
       this.cacheKey = this.constructor.generateCacheKey(this);
       this.cachedAt = new Date();
       return this;
     };

     schema.statics.findCached = async function(query, ttl = 300) {
       const cacheKey = this.generateCacheKey(query);
       
       let result = await RedisCache.get(cacheKey);
       if (result) {
         return result;
       }
       
       result = await this.find(query);
       await RedisCache.set(cacheKey, result, ttl);
       return result;
     };

     schema.statics.generateCacheKey = function(data) {
       return `${this.modelName}:${JSON.stringify(data)}`;
     };
   }

   // Apply plugin to schema
   const ProductSchema = new mongoose.Schema({
     name: String,
     price: Number,
     category: String,
   });

   ProductSchema.plugin(cachePlugin);
   ```

5. **API Response Caching**
   - Implement comprehensive API caching:

   **Express Cache Middleware:**
   ```javascript
   function cacheMiddleware(ttl = 300) {
     return async (req, res, next) => {
       // Only cache GET requests
       if (req.method !== 'GET') {
         return next();
       }

       const cacheKey = `api:${req.originalUrl}`;
       const cached = await RedisCache.get(cacheKey);

       if (cached) {
         return res.json(cached);
       }

       // Override res.json to cache the response
       const originalJson = res.json;
       res.json = function(data) {
         RedisCache.set(cacheKey, data, ttl);
         return originalJson.call(this, data);
       };

       next();
     };
   }

   // Usage
   app.get('/api/dashboard', cacheMiddleware(600), async (req, res) => {
     const dashboardData = await getDashboardData();
     res.json(dashboardData);
   });
   ```

   **GraphQL Query Caching:**
   ```javascript
   const { ApolloServer } = require('apollo-server-express');
   const { ResponseCache } = require('apollo-server-plugin-response-cache');

   const server = new ApolloServer({
     typeDefs,
     resolvers,
     plugins: [
       ResponseCache({
         sessionId: (requestContext) => 
           requestContext.request.http.headers.authorization || null,
         maximumAge: 300, // 5 minutes default
         scope: 'PUBLIC',
       }),
     ],
     cacheControl: {
       defaultMaxAge: 300,
       calculateHttpHeaders: false,
       stripFormattedExtensions: false,
     },
   });

   // Resolver-level caching
   const resolvers = {
     Query: {
       products: async (parent, args, context) => {
         return await DatabaseCache.cachedQuery(
           'SELECT * FROM products WHERE category = $1',
           [args.category],
           600
         );
       },
     },
   };
   ```

6. **Cache Invalidation Strategies**
   - Implement intelligent cache invalidation:

   **Event-Driven Cache Invalidation:**
   ```javascript
   const EventEmitter = require('events');
   const cacheInvalidator = new EventEmitter();

   class CacheInvalidator {
     static invalidateUser(userId) {
       const patterns = [
         `user:${userId}*`,
         `api:/api/users/${userId}*`,
         'api:/api/dashboard*', // If dashboard shows user data
       ];
       
       patterns.forEach(async (pattern) => {
         await RedisCache.invalidatePattern(pattern);
       });
       
       cacheInvalidator.emit('user:updated', userId);
     }

     static invalidateProduct(productId) {
       const patterns = [
         `product:${productId}*`,
         'api:/api/products*',
         'query:*products*',
       ];
       
       patterns.forEach(async (pattern) => {
         await RedisCache.invalidatePattern(pattern);
       });
     }
   }

   // Trigger invalidation on data changes
   app.put('/api/users/:id', async (req, res) => {
     const userId = req.params.id;
     await updateUser(userId, req.body);
     
     // Invalidate related caches
     CacheInvalidator.invalidateUser(userId);
     
     res.json({ success: true });
   });
   ```

7. **Frontend Caching Strategies**
   - Implement client-side caching:

   **React Query Caching:**
   ```javascript
   import { QueryClient, QueryClientProvider, useQuery } from 'react-query';

   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 5 * 60 * 1000, // 5 minutes
         cacheTime: 10 * 60 * 1000, // 10 minutes
         retry: 3,
         refetchOnWindowFocus: false,
       },
     },
   });

   function ProductList() {
     const { data: products, isLoading, error } = useQuery(
       'products',
       () => fetch('/api/products').then(res => res.json()),
       {
         staleTime: 10 * 60 * 1000, // 10 minutes
         cacheTime: 30 * 60 * 1000, // 30 minutes
       }
     );

     if (isLoading) return <div>Loading...</div>;
     if (error) return <div>Error: {error.message}</div>;

     return (
       <div>
         {products.map(product => (
           <div key={product.id}>{product.name}</div>
         ))}
       </div>
     );
   }
   ```

   **Local Storage Caching:**
   ```javascript
   class LocalStorageCache {
     static set(key, value, ttl = 3600000) { // 1 hour default
       const item = {
         value,
         expiry: Date.now() + ttl,
       };
       localStorage.setItem(key, JSON.stringify(item));
     }

     static get(key) {
       const item = localStorage.getItem(key);
       if (!item) return null;

       const parsed = JSON.parse(item);
       if (Date.now() > parsed.expiry) {
         localStorage.removeItem(key);
         return null;
       }

       return parsed.value;
     }

     static remove(key) {
       localStorage.removeItem(key);
     }

     static clear() {
       localStorage.clear();
     }
   }
   ```

8. **Cache Monitoring and Analytics**
   - Set up cache performance monitoring:

   **Cache Metrics Collection:**
   ```javascript
   class CacheMetrics {
     static hits = 0;
     static misses = 0;
     static errors = 0;

     static recordHit() {
       this.hits++;
     }

     static recordMiss() {
       this.misses++;
     }

     static recordError() {
       this.errors++;
     }

     static getStats() {
       const total = this.hits + this.misses;
       return {
         hits: this.hits,
         misses: this.misses,
         errors: this.errors,
         hitRate: total > 0 ? (this.hits / total * 100).toFixed(2) : 0,
         total,
       };
     }

     static reset() {
       this.hits = 0;
       this.misses = 0;
       this.errors = 0;
     }
   }

   // Enhanced cache service with metrics
   class MetricsCache {
     static async get(key) {
       try {
         const value = await RedisCache.get(key);
         if (value !== null) {
           CacheMetrics.recordHit();
         } else {
           CacheMetrics.recordMiss();
         }
         return value;
       } catch (error) {
         CacheMetrics.recordError();
         throw error;
       }
     }
   }

   // Metrics endpoint
   app.get('/api/cache/stats', (req, res) => {
     res.json(CacheMetrics.getStats());
   });
   ```

9. **Cache Warming and Preloading**
   - Implement cache warming strategies:

   **Scheduled Cache Warming:**
   ```javascript
   const cron = require('node-cron');

   class CacheWarmer {
     static async warmPopularData() {
       console.log('Starting cache warming...');
       
       // Warm popular products
       const popularProducts = await DatabaseCache.cachedQuery(
         'SELECT * FROM products ORDER BY view_count DESC LIMIT 100',
         [],
         3600 // 1 hour
       );
       
       // Warm user sessions
       const activeUsers = await DatabaseCache.cachedQuery(
         'SELECT id FROM users WHERE last_active > NOW() - INTERVAL 1 DAY',
         [],
         1800 // 30 minutes
       );
       
       console.log(`Warmed cache for ${popularProducts.length} products and ${activeUsers.length} users`);
     }

     static async warmOnDemand(cacheKeys) {
       for (const key of cacheKeys) {
         if (!(await RedisCache.get(key))) {
           // Generate cache for missing keys
           await this.generateCacheForKey(key);
         }
       }
     }
   }

   // Schedule cache warming
   cron.schedule('0 */6 * * *', () => { // Every 6 hours
     CacheWarmer.warmPopularData();
   });
   ```

10. **Testing and Validation**
    - Set up cache testing and validation:

    **Cache Testing:**
    ```javascript
    // tests/cache.test.js
    const request = require('supertest');
    const app = require('../app');

    describe('Cache Performance', () => {
      test('should cache API responses', async () => {
        // First request - should miss cache
        const start1 = Date.now();
        const response1 = await request(app).get('/api/products');
        const duration1 = Date.now() - start1;

        // Second request - should hit cache
        const start2 = Date.now();
        const response2 = await request(app).get('/api/products');
        const duration2 = Date.now() - start2;

        expect(response1.body).toEqual(response2.body);
        expect(duration2).toBeLessThan(duration1 / 2); // Cached should be faster
      });

      test('should invalidate cache properly', async () => {
        // Get initial data
        const initial = await request(app).get('/api/products');
        
        // Update data
        await request(app)
          .put('/api/products/1')
          .send({ name: 'Updated Product' });
        
        // Should get updated data
        const updated = await request(app).get('/api/products');
        expect(updated.body).not.toEqual(initial.body);
      });
    });
    ```