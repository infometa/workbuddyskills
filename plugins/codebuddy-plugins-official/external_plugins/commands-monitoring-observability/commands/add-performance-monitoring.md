---
description: Setup application performance monitoring
category: monitoring-observability
allowed-tools: Glob
---

# Add Performance Monitoring

Setup application performance monitoring

## Instructions

1. **Performance Monitoring Strategy**
   - Define key performance indicators (KPIs) and service level objectives (SLOs)
   - Identify critical user journeys and performance bottlenecks
   - Plan monitoring architecture and data collection strategy
   - Assess existing monitoring infrastructure and integration points
   - Define alerting thresholds and escalation procedures

2. **Application Performance Monitoring (APM)**
   - Set up comprehensive APM monitoring:

   **Node.js APM with New Relic:**
   ```javascript
   // newrelic.js
   exports.config = {
     app_name: [process.env.NEW_RELIC_APP_NAME || 'My Application'],
     license_key: process.env.NEW_RELIC_LICENSE_KEY,
     distributed_tracing: {
       enabled: true
     },
     transaction_tracer: {
       enabled: true,
       transaction_threshold: 0.5, // 500ms
       record_sql: 'obfuscated',
       explain_threshold: 1000 // 1 second
     },
     error_collector: {
       enabled: true,
       ignore_status_codes: [404, 401]
     },
     browser_monitoring: {
       enable: true
     },
     application_logging: {
       forwarding: {
         enabled: true
       }
     }
   };

   // app.js
   require('newrelic');
   const express = require('express');
   const app = express();

   // Custom metrics
   const newrelic = require('newrelic');

   app.use((req, res, next) => {
     const startTime = Date.now();
     
     res.on('finish', () => {
       const duration = Date.now() - startTime;
       
       // Record custom metrics
       newrelic.recordMetric('Custom/ResponseTime', duration);
       newrelic.recordMetric(`Custom/Endpoint/${req.path}`, duration);
       
       // Add custom attributes
       newrelic.addCustomAttributes({
         'user.id': req.user?.id,
         'request.method': req.method,
         'response.statusCode': res.statusCode
       });
     });
     
     next();
   });
   ```

   **Datadog APM Integration:**
   ```javascript
   // datadog-tracer.js
   const tracer = require('dd-trace').init({
     service: 'my-application',
     env: process.env.NODE_ENV,
     version: process.env.APP_VERSION,
     logInjection: true,
     runtimeMetrics: true,
     profiling: true,
     analytics: true
   });

   // Custom instrumentation
   class PerformanceTracker {
     static startSpan(operationName, options = {}) {
       return tracer.startSpan(operationName, {
         tags: {
           'service.name': 'my-application',
           ...options.tags
         },
         ...options
       });
     }

     static async traceAsync(operationName, asyncFn, tags = {}) {
       const span = this.startSpan(operationName, { tags });
       
       try {
         const result = await asyncFn(span);
         span.setTag('operation.success', true);
         return result;
       } catch (error) {
         span.setTag('operation.success', false);
         span.setTag('error.message', error.message);
         span.setTag('error.stack', error.stack);
         throw error;
       } finally {
         span.finish();
       }
     }

     static trackDatabaseQuery(query, duration, success) {
       tracer.startSpan('database.query', {
         tags: {
           'db.statement': query,
           'db.duration': duration,
           'db.success': success
         }
       }).finish();
     }
   }

   // Usage example
   app.get('/api/users/:id', async (req, res) => {
     await PerformanceTracker.traceAsync('get_user', async (span) => {
       span.setTag('user.id', req.params.id);
       
       const user = await getUserFromDatabase(req.params.id);
       span.setTag('user.found', !!user);
       
       res.json(user);
     }, { endpoint: '/api/users/:id' });
   });
   ```

3. **Real User Monitoring (RUM)**
   - Implement client-side performance tracking:

   **Web Vitals Monitoring:**
   ```javascript
   // performance-monitor.js
   import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

   class RealUserMonitoring {
     constructor() {
       this.metrics = {};
       this.setupWebVitals();
       this.setupCustomMetrics();
     }

     setupWebVitals() {
       getCLS(this.sendMetric.bind(this, 'CLS'));
       getFID(this.sendMetric.bind(this, 'FID'));
       getFCP(this.sendMetric.bind(this, 'FCP'));
       getLCP(this.sendMetric.bind(this, 'LCP'));
       getTTFB(this.sendMetric.bind(this, 'TTFB'));
     }

     setupCustomMetrics() {
       // Track page load performance
       window.addEventListener('load', () => {
         const navigation = performance.getEntriesByType('navigation')[0];
         
         this.sendMetric('page_load_time', {
           name: 'page_load_time',
           value: navigation.loadEventEnd - navigation.fetchStart,
           delta: navigation.loadEventEnd - navigation.fetchStart
         });

         this.sendMetric('dom_content_loaded', {
           name: 'dom_content_loaded',
           value: navigation.domContentLoadedEventEnd - navigation.fetchStart,
           delta: navigation.domContentLoadedEventEnd - navigation.fetchStart
         });
       });

       // Track resource loading
       new PerformanceObserver((list) => {
         for (const entry of list.getEntries()) {
           if (entry.duration > 1000) { // Resources taking >1s
             this.sendMetric('slow_resource', {
               name: 'slow_resource',
               value: entry.duration,
               resource: entry.name,
               type: entry.initiatorType
             });
           }
         }
       }).observe({ entryTypes: ['resource'] });

       // Track user interactions
       ['click', 'keydown', 'touchstart'].forEach(eventType => {
         document.addEventListener(eventType, (event) => {
           const startTime = performance.now();
           
           requestIdleCallback(() => {
             const duration = performance.now() - startTime;
             if (duration > 100) { // Interactions taking >100ms
               this.sendMetric('slow_interaction', {
                 name: 'slow_interaction',
                 value: duration,
                 eventType: eventType,
                 target: event.target.tagName
               });
             }
           });
         });
       });
     }

     sendMetric(metricName, metric) {
       const data = {
         name: metricName,
         value: metric.value,
         delta: metric.delta,
         id: metric.id,
         url: window.location.href,
         userAgent: navigator.userAgent,
         timestamp: Date.now(),
         sessionId: this.getSessionId(),
         userId: this.getUserId()
       };

       // Send to analytics endpoint
       navigator.sendBeacon('/api/metrics', JSON.stringify(data));
     }

     getSessionId() {
       return sessionStorage.getItem('sessionId') || 'anonymous';
     }

     getUserId() {
       return localStorage.getItem('userId') || 'anonymous';
     }
   }

   // Initialize RUM
   new RealUserMonitoring();
   ```

   **React Performance Monitoring:**
   ```javascript
   // react-performance.js
   import { Profiler } from 'react';

   class ReactPerformanceMonitor {
     static ProfilerWrapper = ({ id, children }) => {
       const onRenderCallback = (id, phase, actualDuration, baseDuration, startTime, commitTime) => {
         // Track component render performance
         if (actualDuration > 100) { // Renders taking >100ms
           console.warn(`Slow render detected for ${id}:`, {
             phase,
             actualDuration,
             baseDuration,
             startTime,
             commitTime
           });

           // Send to monitoring service
           fetch('/api/metrics/react-performance', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({
               componentId: id,
               phase,
               actualDuration,
               baseDuration,
               timestamp: Date.now()
             })
           });
         }
       };

       return (
         <Profiler id={id} onRender={onRenderCallback}>
           {children}
         </Profiler>
       );
     };

     static usePerformanceTracking(componentName) {
       useEffect(() => {
         const startTime = performance.now();
         
         return () => {
           const duration = performance.now() - startTime;
           if (duration > 1000) { // Component mounted for >1s
             console.log(`${componentName} lifecycle duration:`, duration);
           }
         };
       }, [componentName]);
     }
   }

   // Usage
   function App() {
     return (
       <ReactPerformanceMonitor.ProfilerWrapper id="App">
         <Dashboard />
         <UserList />
       </ReactPerformanceMonitor.ProfilerWrapper>
     );
   }
   ```

4. **Server Performance Monitoring**
   - Monitor server-side performance metrics:

   **System Metrics Collection:**
   ```javascript
   // system-monitor.js
   const os = require('os');
   const process = require('process');
   const v8 = require('v8');

   class SystemMonitor {
     constructor() {
       this.startTime = Date.now();
       this.intervalId = null;
     }

     start(interval = 30000) { // 30 seconds
       this.intervalId = setInterval(() => {
         this.collectMetrics();
       }, interval);
     }

     stop() {
       if (this.intervalId) {
         clearInterval(this.intervalId);
       }
     }

     collectMetrics() {
       const metrics = {
         // CPU metrics
         cpuUsage: process.cpuUsage(),
         loadAverage: os.loadavg(),
         
         // Memory metrics
         memoryUsage: process.memoryUsage(),
         totalMemory: os.totalmem(),
         freeMemory: os.freemem(),
         
         // V8 heap statistics
         heapStats: v8.getHeapStatistics(),
         heapSpaceStats: v8.getHeapSpaceStatistics(),
         
         // Process metrics
         uptime: process.uptime(),
         pid: process.pid,
         
         // Event loop lag
         eventLoopLag: this.measureEventLoopLag(),
         
         timestamp: Date.now()
       };

       this.sendMetrics(metrics);
     }

     measureEventLoopLag() {
       const start = process.hrtime.bigint();
       setImmediate(() => {
         const lag = Number(process.hrtime.bigint() - start) / 1000000; // Convert to ms
         return lag;
       });
     }

     sendMetrics(metrics) {
       // Send to monitoring service
       console.log('System Metrics:', JSON.stringify(metrics, null, 2));
       
       // Example: Send to StatsD
       // statsd.gauge('system.memory.used', metrics.memoryUsage.used);
       // statsd.gauge('system.cpu.usage', metrics.cpuUsage.system);
     }
   }

   // Start monitoring
   const monitor = new SystemMonitor();
   monitor.start();

   // Graceful shutdown
   process.on('SIGTERM', () => {
     monitor.stop();
     process.exit(0);
   });
   ```

   **Express.js Performance Middleware:**
   ```javascript
   // performance-middleware.js
   const responseTime = require('response-time');
   const promClient = require('prom-client');

   // Prometheus metrics
   const httpRequestDuration = new promClient.Histogram({
     name: 'http_request_duration_seconds',
     help: 'Duration of HTTP requests in seconds',
     labelNames: ['method', 'route', 'status_code'],
     buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10]
   });

   const httpRequestsTotal = new promClient.Counter({
     name: 'http_requests_total',
     help: 'Total number of HTTP requests',
     labelNames: ['method', 'route', 'status_code']
   });

   function performanceMiddleware() {
     return (req, res, next) => {
       const startTime = Date.now();
       const startHrTime = process.hrtime();

       res.on('finish', () => {
         const duration = Date.now() - startTime;
         const hrDuration = process.hrtime(startHrTime);
         const durationSeconds = hrDuration[0] + hrDuration[1] / 1e9;

         const labels = {
           method: req.method,
           route: req.route?.path || req.path,
           status_code: res.statusCode
         };

         // Record Prometheus metrics
         httpRequestDuration.observe(labels, durationSeconds);
         httpRequestsTotal.inc(labels);

         // Log slow requests
         if (duration > 1000) {
           console.warn('Slow request detected:', {
             method: req.method,
             url: req.url,
             duration: duration,
             statusCode: res.statusCode,
             userAgent: req.get('User-Agent'),
             ip: req.ip
           });
         }

         // Track custom metrics
         req.performanceMetrics = {
           duration,
           memoryUsage: process.memoryUsage(),
           cpuUsage: process.cpuUsage()
         };
       });

       next();
     };
   }

   module.exports = { performanceMiddleware, httpRequestDuration, httpRequestsTotal };
   ```

5. **Database Performance Monitoring**
   - Monitor database query performance:

   **Query Performance Tracking:**
   ```javascript
   // db-performance.js
   const { Pool } = require('pg');

   class DatabasePerformanceMonitor {
     constructor(pool) {
       this.pool = pool;
       this.slowQueryThreshold = 1000; // 1 second
       this.queryStats = new Map();
     }

     async executeQuery(query, params = []) {
       const queryId = this.generateQueryId(query);
       const startTime = Date.now();
       const startMemory = process.memoryUsage();

       try {
         const result = await this.pool.query(query, params);
         const duration = Date.now() - startTime;
         const endMemory = process.memoryUsage();

         this.recordQueryMetrics(queryId, query, duration, true, endMemory.heapUsed - startMemory.heapUsed);

         if (duration > this.slowQueryThreshold) {
           this.logSlowQuery(query, params, duration);
         }

         return result;
       } catch (error) {
         const duration = Date.now() - startTime;
         this.recordQueryMetrics(queryId, query, duration, false, 0);
         throw error;
       }
     }

     generateQueryId(query) {
       // Normalize query for grouping similar queries
       return query
         .replace(/\$\d+/g, '?') // Replace parameter placeholders
         .replace(/\s+/g, ' ')   // Normalize whitespace
         .replace(/\d+/g, 'N')   // Replace numbers with 'N'
         .trim()
         .toLowerCase();
     }

     recordQueryMetrics(queryId, query, duration, success, memoryDelta) {
       if (!this.queryStats.has(queryId)) {
         this.queryStats.set(queryId, {
           query: query,
           count: 0,
           totalDuration: 0,
           successCount: 0,
           errorCount: 0,
           averageDuration: 0,
           maxDuration: 0,
           minDuration: Infinity
         });
       }

       const stats = this.queryStats.get(queryId);
       stats.count++;
       stats.totalDuration += duration;
       stats.averageDuration = stats.totalDuration / stats.count;
       stats.maxDuration = Math.max(stats.maxDuration, duration);
       stats.minDuration = Math.min(stats.minDuration, duration);

       if (success) {
         stats.successCount++;
       } else {
         stats.errorCount++;
       }

       // Send metrics to monitoring service
       this.sendQueryMetrics(queryId, duration, success, memoryDelta);
     }

     logSlowQuery(query, params, duration) {
       console.warn('Slow query detected:', {
         query: query,
         params: params,
         duration: duration,
         timestamp: new Date().toISOString()
       });

       // Send alert to monitoring service
       this.sendSlowQueryAlert(query, params, duration);
     }

     sendQueryMetrics(queryId, duration, success, memoryDelta) {
       const metrics = {
         queryId,
         duration,
         success,
         memoryDelta,
         timestamp: Date.now()
       };

       // Send to your monitoring service
       // Example: StatsD, Prometheus, DataDog, etc.
     }

     sendSlowQueryAlert(query, params, duration) {
       // Send to alerting system
       console.log('Sending slow query alert...', { query, duration });
     }

     getQueryStats() {
       return Array.from(this.queryStats.entries()).map(([queryId, stats]) => ({
         queryId,
         ...stats
       }));
     }

     resetStats() {
       this.queryStats.clear();
     }
   }

   // Usage
   const pool = new Pool();
   const dbMonitor = new DatabasePerformanceMonitor(pool);

   // Replace direct pool usage with monitored version
   module.exports = { executeQuery: dbMonitor.executeQuery.bind(dbMonitor) };
   ```

6. **Error Tracking and Monitoring**
   - Implement comprehensive error monitoring:

   **Error Tracking Setup:**
   ```javascript
   // error-monitor.js
   const Sentry = require('@sentry/node');
   const Integrations = require('@sentry/integrations');

   class ErrorMonitor {
     static initialize() {
       Sentry.init({
         dsn: process.env.SENTRY_DSN,
         environment: process.env.NODE_ENV,
         integrations: [
           new Integrations.Http({ tracing: true }),
           new Sentry.Integrations.Express({ app }),
         ],
         tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
         beforeSend(event, hint) {
           // Filter out noise
           if (event.exception) {
             const error = hint.originalException;
             if (error && error.code === 'ECONNABORTED') {
               return null; // Don't send timeout errors
             }
           }
           return event;
         },
         beforeBreadcrumb(breadcrumb) {
           // Filter sensitive data from breadcrumbs
           if (breadcrumb.category === 'http') {
             delete breadcrumb.data?.password;
             delete breadcrumb.data?.token;
           }
           return breadcrumb;
         }
       });
     }

     static captureException(error, context = {}) {
       Sentry.withScope((scope) => {
         Object.keys(context).forEach(key => {
           scope.setContext(key, context[key]);
         });
         Sentry.captureException(error);
       });
     }

     static captureMessage(message, level = 'info', context = {}) {
       Sentry.withScope((scope) => {
         Object.keys(context).forEach(key => {
           scope.setContext(key, context[key]);
         });
         Sentry.captureMessage(message, level);
       });
     }

     static setupExpressErrorHandling(app) {
       // Sentry request handler (must be first)
       app.use(Sentry.Handlers.requestHandler());
       app.use(Sentry.Handlers.tracingHandler());

       // Your routes here

       // Sentry error handler (must be before other error handlers)
       app.use(Sentry.Handlers.errorHandler());

       // Custom error handler
       app.use((error, req, res, next) => {
         const errorId = res.sentry;
         
         console.error('Unhandled error:', {
           errorId,
           error: error.message,
           stack: error.stack,
           url: req.url,
           method: req.method,
           userAgent: req.get('User-Agent'),
           ip: req.ip
         });

         res.status(500).json({
           error: 'Internal server error',
           errorId: errorId
         });
       });
     }
   }

   // Global error handlers
   process.on('uncaughtException', (error) => {
     console.error('Uncaught Exception:', error);
     ErrorMonitor.captureException(error, { type: 'uncaughtException' });
     process.exit(1);
   });

   process.on('unhandledRejection', (reason, promise) => {
     console.error('Unhandled Rejection at:', promise, 'reason:', reason);
     ErrorMonitor.captureException(new Error(reason), { type: 'unhandledRejection' });
   });
   ```

7. **Custom Metrics and Dashboards**
   - Create custom performance dashboards:

   **Prometheus Metrics:**
   ```javascript
   // prometheus-metrics.js
   const promClient = require('prom-client');

   class CustomMetrics {
     constructor() {
       // Register default metrics
       promClient.register.setDefaultLabels({
         app: process.env.APP_NAME || 'my-app',
         version: process.env.APP_VERSION || '1.0.0'
       });
       promClient.collectDefaultMetrics();

       this.setupCustomMetrics();
     }

     setupCustomMetrics() {
       // Business metrics
       this.userRegistrations = new promClient.Counter({
         name: 'user_registrations_total',
         help: 'Total number of user registrations',
         labelNames: ['source', 'plan']
       });

       this.orderValue = new promClient.Histogram({
         name: 'order_value_dollars',
         help: 'Order value in dollars',
         labelNames: ['currency', 'payment_method'],
         buckets: [10, 50, 100, 500, 1000, 5000]
       });

       this.cacheHitRate = new promClient.Gauge({
         name: 'cache_hit_rate',
         help: 'Cache hit rate percentage',
         labelNames: ['cache_type']
       });

       this.activeUsers = new promClient.Gauge({
         name: 'active_users_current',
         help: 'Currently active users',
         labelNames: ['session_type']
       });

       // Performance metrics
       this.databaseConnectionPool = new promClient.Gauge({
         name: 'database_connections_active',
         help: 'Active database connections',
         labelNames: ['pool_name']
       });

       this.apiResponseTime = new promClient.Histogram({
         name: 'api_response_time_seconds',
         help: 'API response time in seconds',
         labelNames: ['endpoint', 'method', 'status'],
         buckets: [0.1, 0.5, 1, 2, 5, 10]
       });
     }

     // Helper methods
     recordUserRegistration(source, plan) {
       this.userRegistrations.inc({ source, plan });
     }

     recordOrderValue(value, currency, paymentMethod) {
       this.orderValue.observe({ currency, payment_method: paymentMethod }, value);
     }

     updateCacheHitRate(cacheType, hitRate) {
       this.cacheHitRate.set({ cache_type: cacheType }, hitRate);
     }

     setActiveUsers(count, sessionType = 'web') {
       this.activeUsers.set({ session_type: sessionType }, count);
     }

     getMetrics() {
       return promClient.register.metrics();
     }
   }

   const metrics = new CustomMetrics();

   // Metrics endpoint
   app.get('/metrics', async (req, res) => {
     res.set('Content-Type', promClient.register.contentType);
     res.end(await metrics.getMetrics());
   });

   module.exports = metrics;
   ```

8. **Alerting and Notification System**
   - Set up intelligent alerting:

   **Alert Manager:**
   ```javascript
   // alert-manager.js
   const nodemailer = require('nodemailer');
   const slack = require('@slack/webhook');

   class AlertManager {
     constructor() {
       this.emailTransporter = nodemailer.createTransporter({
         // Email configuration
       });
       
       this.slackWebhook = new slack.IncomingWebhook(process.env.SLACK_WEBHOOK_URL);
       
       this.alertThresholds = {
         responseTime: 2000, // 2 seconds
         errorRate: 0.05,    // 5%
         cpuUsage: 0.8,      // 80%
         memoryUsage: 0.9,   // 90%
         diskUsage: 0.85     // 85%
       };
       
       this.alertCooldowns = new Map();
     }

     async checkPerformanceThresholds(metrics) {
       const alerts = [];

       // Response time alert
       if (metrics.averageResponseTime > this.alertThresholds.responseTime) {
         alerts.push({
           severity: 'warning',
           metric: 'response_time',
           current: metrics.averageResponseTime,
           threshold: this.alertThresholds.responseTime,
           message: `Average response time is ${metrics.averageResponseTime}ms (threshold: ${this.alertThresholds.responseTime}ms)`
         });
       }

       // Error rate alert
       if (metrics.errorRate > this.alertThresholds.errorRate) {
         alerts.push({
           severity: 'critical',
           metric: 'error_rate',
           current: metrics.errorRate,
           threshold: this.alertThresholds.errorRate,
           message: `Error rate is ${(metrics.errorRate * 100).toFixed(2)}% (threshold: ${(this.alertThresholds.errorRate * 100)}%)`
         });
       }

       // System resource alerts
       if (metrics.cpuUsage > this.alertThresholds.cpuUsage) {
         alerts.push({
           severity: 'warning',
           metric: 'cpu_usage',
           current: metrics.cpuUsage,
           threshold: this.alertThresholds.cpuUsage,
           message: `CPU usage is ${(metrics.cpuUsage * 100).toFixed(1)}% (threshold: ${(this.alertThresholds.cpuUsage * 100)}%)`
         });
       }

       // Send alerts
       for (const alert of alerts) {
         await this.sendAlert(alert);
       }
     }

     async sendAlert(alert) {
       const alertKey = `${alert.metric}_${alert.severity}`;
       const now = Date.now();
       const cooldownPeriod = alert.severity === 'critical' ? 300000 : 900000; // 5min for critical, 15min for others

       // Check cooldown
       if (this.alertCooldowns.has(alertKey)) {
         const lastAlert = this.alertCooldowns.get(alertKey);
         if (now - lastAlert < cooldownPeriod) {
           return; // Skip this alert due to cooldown
         }
       }

       this.alertCooldowns.set(alertKey, now);

       // Send to multiple channels
       await Promise.all([
         this.sendSlackAlert(alert),
         this.sendEmailAlert(alert),
         this.logAlert(alert)
       ]);
     }

     async sendSlackAlert(alert) {
       const color = alert.severity === 'critical' ? 'danger' : 'warning';
       const emoji = alert.severity === 'critical' ? ':rotating_light:' : ':warning:';
       
       await this.slackWebhook.send({
         text: `${emoji} Performance Alert`,
         attachments: [{
           color: color,
           fields: [
             { title: 'Metric', value: alert.metric, short: true },
             { title: 'Severity', value: alert.severity, short: true },
             { title: 'Current Value', value: alert.current.toString(), short: true },
             { title: 'Threshold', value: alert.threshold.toString(), short: true },
             { title: 'Message', value: alert.message, short: false }
           ],
           ts: Math.floor(Date.now() / 1000)
         }]
       });
     }

     async sendEmailAlert(alert) {
       if (alert.severity === 'critical') {
         await this.emailTransporter.sendMail({
           to: process.env.ALERT_EMAIL,
           subject: `CRITICAL: ${alert.metric} alert`,
           html: `
             <h2>Performance Alert</h2>
             <p><strong>Severity:</strong> ${alert.severity}</p>
             <p><strong>Metric:</strong> ${alert.metric}</p>
             <p><strong>Message:</strong> ${alert.message}</p>
             <p><strong>Current Value:</strong> ${alert.current}</p>
             <p><strong>Threshold:</strong> ${alert.threshold}</p>
             <p><strong>Time:</strong> ${new Date().toISOString()}</p>
           `
         });
       }
     }

     logAlert(alert) {
       console.error('PERFORMANCE ALERT:', {
         timestamp: new Date().toISOString(),
         severity: alert.severity,
         metric: alert.metric,
         current: alert.current,
         threshold: alert.threshold,
         message: alert.message
       });
     }
   }

   module.exports = AlertManager;
   ```

9. **Performance Testing Integration**
   - Integrate with performance testing:

   **Load Test Monitoring:**
   ```javascript
   // load-test-monitor.js
   class LoadTestMonitor {
     constructor() {
       this.testResults = [];
       this.baselineMetrics = null;
     }

     async runPerformanceTest(testConfig) {
       console.log('Starting performance test...', testConfig);
       
       const startMetrics = await this.captureSystemMetrics();
       const startTime = Date.now();

       try {
         // Run the actual load test (using k6, artillery, etc.)
         const testResults = await this.executeLoadTest(testConfig);
         
         const endTime = Date.now();
         const endMetrics = await this.captureSystemMetrics();

         const result = {
           testId: this.generateTestId(),
           config: testConfig,
           duration: endTime - startTime,
           startMetrics,
           endMetrics,
           testResults,
           timestamp: new Date().toISOString()
         };

         this.testResults.push(result);
         await this.analyzeResults(result);
         
         return result;
       } catch (error) {
         console.error('Load test failed:', error);
         throw error;
       }
     }

     async captureSystemMetrics() {
       return {
         cpu: os.loadavg(),
         memory: {
           total: os.totalmem(),
           free: os.freemem(),
           used: os.totalmem() - os.freemem()
         },
         processes: await this.getProcessMetrics()
       };
     }

     async analyzeResults(result) {
       const analysis = {
         performanceRegression: false,
         recommendations: []
       };

       // Compare with baseline
       if (this.baselineMetrics) {
         const responseTimeIncrease = (result.testResults.averageResponseTime - this.baselineMetrics.averageResponseTime) / this.baselineMetrics.averageResponseTime;
         
         if (responseTimeIncrease > 0.2) { // 20% increase
           analysis.performanceRegression = true;
           analysis.recommendations.push(`Response time increased by ${(responseTimeIncrease * 100).toFixed(1)}%`);
         }
       }

       // Resource utilization analysis
       const maxCpuUsage = Math.max(...result.endMetrics.cpu);
       if (maxCpuUsage > 0.8) {
         analysis.recommendations.push('High CPU usage detected - consider scaling');
       }

       const memoryUsagePercent = result.endMetrics.memory.used / result.endMetrics.memory.total;
       if (memoryUsagePercent > 0.9) {
         analysis.recommendations.push('High memory usage detected - check for memory leaks');
       }

       console.log('Performance test analysis:', analysis);
       return analysis;
     }

     setBaseline(testResult) {
       this.baselineMetrics = testResult.testResults;
       console.log('Baseline metrics set:', this.baselineMetrics);
     }

     generateTestId() {
       return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
     }
   }
   ```

10. **Performance Optimization Recommendations**
    - Generate actionable performance insights:

    **Performance Analyzer:**
    ```javascript
    // performance-analyzer.js
    class PerformanceAnalyzer {
      constructor() {
        this.metrics = [];
        this.thresholds = {
          responseTime: { good: 200, warning: 1000, critical: 3000 },
          memoryUsage: { good: 0.6, warning: 0.8, critical: 0.9 },
          cpuUsage: { good: 0.5, warning: 0.7, critical: 0.85 },
          errorRate: { good: 0.01, warning: 0.05, critical: 0.1 }
        };
      }

      analyzePerformance(metrics) {
        const recommendations = [];
        const scores = {};

        // Analyze response time
        if (metrics.averageResponseTime > this.thresholds.responseTime.critical) {
          recommendations.push({
            priority: 'high',
            category: 'response_time',
            issue: 'Very slow response times detected',
            recommendations: [
              'Implement database query optimization',
              'Add caching layer (Redis/Memcached)',
              'Enable CDN for static assets',
              'Consider horizontal scaling'
            ],
            impact: 'Critical user experience impact'
          });
          scores.responseTime = 1;
        } else if (metrics.averageResponseTime > this.thresholds.responseTime.warning) {
          recommendations.push({
            priority: 'medium',
            category: 'response_time',
            issue: 'Moderate response time issues',
            recommendations: [
              'Optimize database queries',
              'Implement query result caching',
              'Review N+1 query patterns'
            ],
            impact: 'Moderate user experience impact'
          });
          scores.responseTime = 6;
        } else {
          scores.responseTime = 10;
        }

        // Analyze memory usage
        if (metrics.memoryUsage > this.thresholds.memoryUsage.critical) {
          recommendations.push({
            priority: 'high',
            category: 'memory',
            issue: 'Critical memory usage',
            recommendations: [
              'Check for memory leaks',
              'Implement garbage collection tuning',
              'Add more memory or scale horizontally',
              'Review large object allocations'
            ],
            impact: 'Risk of application crashes'
          });
          scores.memory = 2;
        }

        // Analyze error rate
        if (metrics.errorRate > this.thresholds.errorRate.critical) {
          recommendations.push({
            priority: 'high',
            category: 'reliability',
            issue: 'High error rate detected',
            recommendations: [
              'Review application logs for error patterns',
              'Implement circuit breakers',
              'Add retry mechanisms',
              'Improve error handling'
            ],
            impact: 'Significant functionality issues'
          });
          scores.reliability = 3;
        }

        const overallScore = Object.values(scores).reduce((a, b) => a + b, 0) / Object.keys(scores).length;

        return {
          overallScore: Math.round(overallScore),
          grade: this.getPerformanceGrade(overallScore),
          recommendations: recommendations.sort((a, b) => {
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            return priorityOrder[b.priority] - priorityOrder[a.priority];
          }),
          metrics,
          timestamp: new Date().toISOString()
        };
      }

      getPerformanceGrade(score) {
        if (score >= 9) return 'A';
        if (score >= 8) return 'B';
        if (score >= 7) return 'C';
        if (score >= 6) return 'D';
        return 'F';
      }

      generateReport(analysis) {
        return {
          summary: {
            grade: analysis.grade,
            score: analysis.overallScore,
            criticalIssues: analysis.recommendations.filter(r => r.priority === 'high').length,
            totalRecommendations: analysis.recommendations.length
          },
          keyMetrics: {
            responseTime: analysis.metrics.averageResponseTime,
            errorRate: (analysis.metrics.errorRate * 100).toFixed(2) + '%',
            memoryUsage: (analysis.metrics.memoryUsage * 100).toFixed(1) + '%',
            cpuUsage: (analysis.metrics.cpuUsage * 100).toFixed(1) + '%'
          },
          recommendations: analysis.recommendations,
          generatedAt: analysis.timestamp
        };
      }
    }

    module.exports = PerformanceAnalyzer;
    ```