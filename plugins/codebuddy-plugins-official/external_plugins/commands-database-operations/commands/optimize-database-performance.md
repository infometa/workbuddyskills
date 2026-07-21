---
description: Optimize database queries and performance
category: database-operations
allowed-tools: Read, Write
---

# Optimize Database Performance

Optimize database queries and performance

## Instructions

1. **Database Performance Analysis**
   - Analyze current database performance and identify bottlenecks
   - Review slow query logs and execution plans
   - Assess database schema design and normalization
   - Evaluate indexing strategy and query patterns
   - Monitor database resource utilization (CPU, memory, I/O)

2. **Query Optimization**
   - Optimize slow queries and improve execution plans:

   **PostgreSQL Query Optimization:**
   ```sql
   -- Enable query logging for analysis
   ALTER SYSTEM SET log_statement = 'all';
   ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries > 1 second
   SELECT pg_reload_conf();

   -- Analyze query performance
   EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
   SELECT u.id, u.name, COUNT(o.id) as order_count
   FROM users u
   LEFT JOIN orders o ON u.id = o.user_id
   WHERE u.created_at > '2023-01-01'
   GROUP BY u.id, u.name
   ORDER BY order_count DESC;

   -- Optimize with proper indexing
   CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);
   CREATE INDEX CONCURRENTLY idx_orders_user_id ON orders(user_id);
   CREATE INDEX CONCURRENTLY idx_orders_user_created ON orders(user_id, created_at);
   ```

   **MySQL Query Optimization:**
   ```sql
   -- Enable slow query log
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;
   SET GLOBAL log_queries_not_using_indexes = 'ON';

   -- Analyze query performance
   EXPLAIN FORMAT=JSON 
   SELECT p.*, c.name as category_name
   FROM products p
   JOIN categories c ON p.category_id = c.id
   WHERE p.price BETWEEN 100 AND 500
   AND p.created_at > DATE_SUB(NOW(), INTERVAL 30 DAY);

   -- Add composite indexes
   ALTER TABLE products 
   ADD INDEX idx_price_created (price, created_at),
   ADD INDEX idx_category_price (category_id, price);
   ```

3. **Index Strategy Optimization**
   - Design and implement optimal indexing strategy:

   **Index Analysis and Creation:**
   ```sql
   -- PostgreSQL index usage analysis
   SELECT 
     schemaname,
     tablename,
     indexname,
     idx_scan as index_scans,
     seq_scan as table_scans,
     idx_scan::float / (idx_scan + seq_scan + 1) as index_usage_ratio
   FROM pg_stat_user_indexes 
   ORDER BY index_usage_ratio ASC;

   -- Find missing indexes
   SELECT 
     query,
     calls,
     total_time,
     mean_time,
     rows
   FROM pg_stat_statements 
   WHERE mean_time > 1000 -- queries taking > 1 second
   ORDER BY mean_time DESC;

   -- Create covering indexes for common query patterns
   CREATE INDEX CONCURRENTLY idx_orders_covering 
   ON orders(user_id, status, created_at) 
   INCLUDE (total_amount, discount);

   -- Partial indexes for selective conditions
   CREATE INDEX CONCURRENTLY idx_active_users 
   ON users(last_login) 
   WHERE status = 'active';
   ```

   **Index Maintenance Scripts:**
   ```javascript
   // Node.js index analysis tool
   const { Pool } = require('pg');
   const pool = new Pool();

   class IndexAnalyzer {
     static async analyzeUnusedIndexes() {
       const query = `
         SELECT 
           schemaname,
           tablename,
           indexname,
           idx_scan,
           pg_size_pretty(pg_relation_size(indexrelid)) as size
         FROM pg_stat_user_indexes 
         WHERE idx_scan = 0
         AND schemaname = 'public'
         ORDER BY pg_relation_size(indexrelid) DESC;
       `;
       
       const result = await pool.query(query);
       console.log('Unused indexes:', result.rows);
       return result.rows;
     }

     static async suggestIndexes() {
       const query = `
         SELECT 
           query,
           calls,
           total_time,
           mean_time
         FROM pg_stat_statements 
         WHERE mean_time > 100
         AND query NOT LIKE '%pg_%'
         ORDER BY total_time DESC
         LIMIT 20;
       `;
       
       const result = await pool.query(query);
       console.log('Slow queries needing indexes:', result.rows);
       return result.rows;
     }
   }
   ```

4. **Schema Design Optimization**
   - Optimize database schema for performance:

   **Normalization and Denormalization:**
   ```sql
   -- Denormalization example for read-heavy workloads
   -- Instead of joining multiple tables for product display
   CREATE TABLE product_display_cache AS
   SELECT 
     p.id,
     p.name,
     p.price,
     p.description,
     c.name as category_name,
     b.name as brand_name,
     AVG(r.rating) as avg_rating,
     COUNT(r.id) as review_count
   FROM products p
   JOIN categories c ON p.category_id = c.id
   JOIN brands b ON p.brand_id = b.id
   LEFT JOIN reviews r ON p.id = r.product_id
   GROUP BY p.id, c.name, b.name;

   -- Create materialized view for complex aggregations
   CREATE MATERIALIZED VIEW monthly_sales_summary AS
   SELECT 
     DATE_TRUNC('month', created_at) as month,
     category_id,
     COUNT(*) as order_count,
     SUM(total_amount) as total_revenue,
     AVG(total_amount) as avg_order_value
   FROM orders 
   WHERE created_at >= DATE_TRUNC('year', CURRENT_DATE)
   GROUP BY DATE_TRUNC('month', created_at), category_id;

   -- Refresh materialized view periodically
   REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_sales_summary;
   ```

   **Partitioning for Large Tables:**
   ```sql
   -- PostgreSQL table partitioning
   CREATE TABLE orders_partitioned (
     id SERIAL,
     user_id INTEGER,
     total_amount DECIMAL(10,2),
     created_at TIMESTAMP NOT NULL,
     status VARCHAR(50)
   ) PARTITION BY RANGE (created_at);

   -- Create monthly partitions
   CREATE TABLE orders_2024_01 PARTITION OF orders_partitioned
   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

   CREATE TABLE orders_2024_02 PARTITION OF orders_partitioned
   FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

   -- Automatic partition creation
   CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
   RETURNS void AS $$
   DECLARE
     partition_name text;
     end_date date;
   BEGIN
     partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
     end_date := start_date + interval '1 month';
     
     EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
       partition_name, table_name, start_date, end_date);
   END;
   $$ LANGUAGE plpgsql;
   ```

5. **Connection Pool Optimization**
   - Configure optimal database connection pooling:

   **Node.js Connection Pool Configuration:**
   ```javascript
   const { Pool } = require('pg');

   // Optimized connection pool configuration
   const pool = new Pool({
     user: process.env.DB_USER,
     host: process.env.DB_HOST,
     database: process.env.DB_NAME,
     password: process.env.DB_PASSWORD,
     port: process.env.DB_PORT,
     
     // Connection pool settings
     max: 20, // Maximum connections
     idleTimeoutMillis: 30000, // 30 seconds
     connectionTimeoutMillis: 2000, // 2 seconds
     maxUses: 7500, // Max uses before connection refresh
     
     // Performance settings
     statement_timeout: 30000, // 30 seconds
     query_timeout: 30000,
     
     // SSL configuration
     ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
   });

   // Connection pool monitoring
   pool.on('connect', (client) => {
     console.log('Connected to database');
   });

   pool.on('error', (err, client) => {
     console.error('Database connection error:', err);
   });

   // Pool stats monitoring
   setInterval(() => {
     console.log('Pool stats:', {
       totalCount: pool.totalCount,
       idleCount: pool.idleCount,
       waitingCount: pool.waitingCount,
     });
   }, 60000); // Every minute
   ```

   **Database Connection Middleware:**
   ```javascript
   class DatabaseManager {
     static async executeQuery(query, params = []) {
       const client = await pool.connect();
       try {
         const start = Date.now();
         const result = await client.query(query, params);
         const duration = Date.now() - start;
         
         // Log slow queries
         if (duration > 1000) {
           console.warn(`Slow query (${duration}ms):`, query);
         }
         
         return result;
       } finally {
         client.release();
       }
     }

     static async transaction(callback) {
       const client = await pool.connect();
       try {
         await client.query('BEGIN');
         const result = await callback(client);
         await client.query('COMMIT');
         return result;
       } catch (error) {
         await client.query('ROLLBACK');
         throw error;
       } finally {
         client.release();
       }
     }
   }
   ```

6. **Query Result Caching**
   - Implement intelligent database result caching:

   ```javascript
   const Redis = require('redis');
   const redis = Redis.createClient();

   class QueryCache {
     static generateKey(query, params) {
       return `query:${Buffer.from(query + JSON.stringify(params)).toString('base64')}`;
     }

     static async get(query, params) {
       const key = this.generateKey(query, params);
       const cached = await redis.get(key);
       return cached ? JSON.parse(cached) : null;
     }

     static async set(query, params, result, ttl = 300) {
       const key = this.generateKey(query, params);
       await redis.setex(key, ttl, JSON.stringify(result));
     }

     static async cachedQuery(query, params = [], ttl = 300) {
       // Try cache first
       let result = await this.get(query, params);
       if (result) {
         return result;
       }

       // Execute query and cache result
       result = await DatabaseManager.executeQuery(query, params);
       await this.set(query, params, result.rows, ttl);
       
       return result;
     }

     // Cache invalidation by table patterns
     static async invalidateTable(tableName) {
       const pattern = `query:*${tableName}*`;
       const keys = await redis.keys(pattern);
       if (keys.length > 0) {
         await redis.del(keys);
       }
     }
   }
   ```

7. **Database Monitoring and Profiling**
   - Set up comprehensive database monitoring:

   **Performance Monitoring Script:**
   ```javascript
   class DatabaseMonitor {
     static async getPerformanceStats() {
       const queries = [
         {
           name: 'active_connections',
           query: 'SELECT count(*) FROM pg_stat_activity WHERE state = \'active\';'
         },
         {
           name: 'long_running_queries',
           query: `SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
                   FROM pg_stat_activity 
                   WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';`
         },
         {
           name: 'table_sizes',
           query: `SELECT relname AS table_name, 
                          pg_size_pretty(pg_total_relation_size(relid)) AS size
                   FROM pg_catalog.pg_statio_user_tables 
                   ORDER BY pg_total_relation_size(relid) DESC LIMIT 10;`
         },
         {
           name: 'index_usage',
           query: `SELECT relname AS table_name, 
                          indexrelname AS index_name,
                          idx_scan AS index_scans,
                          seq_scan AS sequential_scans
                   FROM pg_stat_user_indexes 
                   WHERE seq_scan > idx_scan;`
         }
       ];

       const stats = {};
       for (const { name, query } of queries) {
         try {
           const result = await pool.query(query);
           stats[name] = result.rows;
         } catch (error) {
           stats[name] = { error: error.message };
         }
       }

       return stats;
     }

     static async alertOnSlowQueries() {
       const slowQueries = await pool.query(`
         SELECT query, calls, total_time, mean_time, stddev_time
         FROM pg_stat_statements 
         WHERE mean_time > 1000 
         ORDER BY mean_time DESC 
         LIMIT 10;
       `);

       if (slowQueries.rows.length > 0) {
         console.warn('Slow queries detected:', slowQueries.rows);
         // Send alert to monitoring system
       }
     }
   }

   // Schedule monitoring
   setInterval(async () => {
     await DatabaseMonitor.alertOnSlowQueries();
   }, 300000); // Every 5 minutes
   ```

8. **Read Replica and Load Balancing**
   - Configure read replicas for query distribution:

   ```javascript
   const { Pool } = require('pg');

   class DatabaseCluster {
     constructor() {
       this.writePool = new Pool({
         host: process.env.DB_WRITE_HOST,
         // ... write database config
       });

       this.readPools = [
         new Pool({
           host: process.env.DB_READ1_HOST,
           // ... read replica 1 config
         }),
         new Pool({
           host: process.env.DB_READ2_HOST,
           // ... read replica 2 config
         }),
       ];

       this.currentReadIndex = 0;
     }

     getReadPool() {
       // Round-robin read replica selection
       const pool = this.readPools[this.currentReadIndex];
       this.currentReadIndex = (this.currentReadIndex + 1) % this.readPools.length;
       return pool;
     }

     async executeWrite(query, params) {
       return await this.writePool.query(query, params);
     }

     async executeRead(query, params) {
       const readPool = this.getReadPool();
       return await readPool.query(query, params);
     }

     async executeQuery(query, params, forceWrite = false) {
       const isWriteQuery = /^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)/i.test(query);
       
       if (isWriteQuery || forceWrite) {
         return await this.executeWrite(query, params);
       } else {
         return await this.executeRead(query, params);
       }
     }
   }

   const dbCluster = new DatabaseCluster();
   ```

9. **Database Vacuum and Maintenance**
   - Implement automated database maintenance:

   **PostgreSQL Maintenance Scripts:**
   ```sql
   -- Automated vacuum and analyze
   CREATE OR REPLACE FUNCTION auto_vacuum_analyze()
   RETURNS void AS $$
   DECLARE
     rec RECORD;
   BEGIN
     FOR rec IN 
       SELECT schemaname, tablename 
       FROM pg_tables 
       WHERE schemaname = 'public'
     LOOP
       EXECUTE 'VACUUM ANALYZE ' || quote_ident(rec.schemaname) || '.' || quote_ident(rec.tablename);
       RAISE NOTICE 'Vacuumed table %.%', rec.schemaname, rec.tablename;
     END LOOP;
   END;
   $$ LANGUAGE plpgsql;

   -- Schedule maintenance (using pg_cron extension)
   SELECT cron.schedule('nightly-maintenance', '0 2 * * *', 'SELECT auto_vacuum_analyze();');
   ```

   **Maintenance Monitoring:**
   ```javascript
   class MaintenanceMonitor {
     static async checkTableBloat() {
       const query = `
         SELECT 
           tablename,
           pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
           n_dead_tup,
           n_live_tup,
           CASE 
             WHEN n_live_tup > 0 
             THEN round(n_dead_tup::numeric / n_live_tup::numeric, 2) 
             ELSE 0 
           END as dead_ratio
         FROM pg_stat_user_tables 
         WHERE n_dead_tup > 1000
         ORDER BY dead_ratio DESC;
       `;

       const result = await pool.query(query);
       
       // Alert if dead tuple ratio is high
       result.rows.forEach(row => {
         if (row.dead_ratio > 0.2) {
           console.warn(`Table ${row.tablename} has high bloat: ${row.dead_ratio}`);
         }
       });

       return result.rows;
     }

     static async reindexIfNeeded() {
       const bloatedIndexes = await pool.query(`
         SELECT indexname, tablename 
         FROM pg_stat_user_indexes 
         WHERE idx_scan = 0 AND pg_relation_size(indexrelid) > 10485760; -- > 10MB
       `);

       // Suggest reindexing unused large indexes
       bloatedIndexes.rows.forEach(row => {
         console.log(`Consider dropping unused index: ${row.indexname} on ${row.tablename}`);
       });
     }
   }
   ```

10. **Performance Testing and Benchmarking**
    - Set up database performance testing:

    **Load Testing Script:**
    ```javascript
    const { Pool } = require('pg');
    const pool = new Pool();

    class DatabaseLoadTester {
      static async benchmarkQuery(query, params, iterations = 100) {
        const times = [];
        
        for (let i = 0; i < iterations; i++) {
          const start = process.hrtime.bigint();
          await pool.query(query, params);
          const end = process.hrtime.bigint();
          
          times.push(Number(end - start) / 1000000); // Convert to milliseconds
        }

        const avg = times.reduce((a, b) => a + b, 0) / times.length;
        const min = Math.min(...times);
        const max = Math.max(...times);
        const median = times.sort()[Math.floor(times.length / 2)];

        return { avg, min, max, median, iterations };
      }

      static async stressTest(concurrency = 10, duration = 60000) {
        const startTime = Date.now();
        const results = { success: 0, errors: 0, totalTime: 0 };
        
        const workers = Array(concurrency).fill().map(async () => {
          while (Date.now() - startTime < duration) {
            try {
              const start = Date.now();
              await pool.query('SELECT COUNT(*) FROM products');
              results.totalTime += Date.now() - start;
              results.success++;
            } catch (error) {
              results.errors++;
            }
          }
        });

        await Promise.all(workers);
        
        results.qps = results.success / (duration / 1000);
        results.avgResponseTime = results.totalTime / results.success;
        
        return results;
      }
    }

    // Run benchmarks
    async function runBenchmarks() {
      console.log('Running database benchmarks...');
      
      const simpleQuery = await DatabaseLoadTester.benchmarkQuery(
        'SELECT * FROM products LIMIT 10'
      );
      console.log('Simple query benchmark:', simpleQuery);
      
      const complexQuery = await DatabaseLoadTester.benchmarkQuery(
        `SELECT p.*, c.name as category 
         FROM products p 
         JOIN categories c ON p.category_id = c.id 
         ORDER BY p.created_at DESC LIMIT 50`
      );
      console.log('Complex query benchmark:', complexQuery);
      
      const stressTest = await DatabaseLoadTester.stressTest(5, 30000);
      console.log('Stress test results:', stressTest);
    }
    ```