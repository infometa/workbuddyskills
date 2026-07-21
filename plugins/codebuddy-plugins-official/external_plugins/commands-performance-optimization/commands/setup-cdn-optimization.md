---
description: Configure CDN for optimal delivery
category: performance-optimization
---

# Setup CDN Optimization

Configure CDN for optimal delivery

## Instructions

1. **CDN Strategy and Provider Selection**
   - Analyze application traffic patterns and global user distribution
   - Evaluate CDN providers (CloudFlare, AWS CloudFront, Fastly, KeyCDN)
   - Assess content types and caching requirements
   - Plan CDN architecture and edge location strategy
   - Define performance and cost optimization goals

2. **CDN Configuration and Setup**
   - Configure CDN with optimal settings:

   **CloudFlare Configuration:**
   ```javascript
   // Cloudflare Page Rules via API
   const cloudflare = require('cloudflare');
   const cf = new cloudflare({
     email: process.env.CLOUDFLARE_EMAIL,
     key: process.env.CLOUDFLARE_API_KEY
   });

   const pageRules = [
     {
       targets: [{ target: 'url', constraint: { operator: 'matches', value: '*/static/*' }}],
       actions: [
         { id: 'cache_level', value: 'cache_everything' },
         { id: 'edge_cache_ttl', value: 31536000 }, // 1 year
         { id: 'browser_cache_ttl', value: 31536000 }
       ]
     },
     {
       targets: [{ target: 'url', constraint: { operator: 'matches', value: '*/api/*' }}],
       actions: [
         { id: 'cache_level', value: 'bypass' },
         { id: 'compression', value: 'gzip' }
       ]
     }
   ];

   async function setupCDNRules() {
     for (const rule of pageRules) {
       await cf.zones.pagerules.add(process.env.CLOUDFLARE_ZONE_ID, rule);
     }
   }
   ```

   **AWS CloudFront Distribution:**
   ```yaml
   # cloudformation-cdn.yaml
   AWSTemplateFormatVersion: '2010-09-09'
   Resources:
     CloudFrontDistribution:
       Type: AWS::CloudFront::Distribution
       Properties:
         DistributionConfig:
           Origins:
             - Id: S3Origin
               DomainName: !GetAtt S3Bucket.DomainName
               S3OriginConfig:
                 OriginAccessIdentity: !Sub 'origin-access-identity/cloudfront/${OAI}'
             - Id: APIOrigin
               DomainName: api.example.com
               CustomOriginConfig:
                 HTTPPort: 443
                 OriginProtocolPolicy: https-only
           
           DefaultCacheBehavior:
             TargetOriginId: S3Origin
             ViewerProtocolPolicy: redirect-to-https
             CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad # Managed-CachingOptimized
             OriginRequestPolicyId: 88a5eaf4-2fd4-4709-b370-b4c650ea3fcf # Managed-CORS-S3Origin
             
           CacheBehaviors:
             - PathPattern: '/api/*'
               TargetOriginId: APIOrigin
               ViewerProtocolPolicy: https-only
               CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
               TTL:
                 DefaultTTL: 0
                 MaxTTL: 0
               Compress: true
             
             - PathPattern: '/static/*'
               TargetOriginId: S3Origin
               ViewerProtocolPolicy: https-only
               CachePolicyId: 658327ea-f89d-4fab-a63d-7e88639e58f6 # Managed-CachingOptimizedForUncompressedObjects
               TTL:
                 DefaultTTL: 86400
                 MaxTTL: 31536000
   ```

3. **Static Asset Optimization**
   - Optimize assets for CDN delivery:

   **Asset Build Process:**
   ```javascript
   // webpack.config.js - CDN optimization
   const path = require('path');
   const { CleanWebpackPlugin } = require('clean-webpack-plugin');
   const MiniCssExtractPlugin = require('mini-css-extract-plugin');

   module.exports = {
     output: {
       path: path.resolve(__dirname, 'dist'),
       filename: '[name].[contenthash].js',
       publicPath: process.env.CDN_URL || '/',
       assetModuleFilename: 'assets/[name].[contenthash][ext]',
     },
     
     optimization: {
       splitChunks: {
         chunks: 'all',
         cacheGroups: {
           vendor: {
             test: /[\\/]node_modules[\\/]/,
             name: 'vendors',
             filename: 'vendors.[contenthash].js',
           },
         },
       },
     },
     
     plugins: [
       new CleanWebpackPlugin(),
       new MiniCssExtractPlugin({
         filename: 'css/[name].[contenthash].css',
       }),
     ],
     
     module: {
       rules: [
         {
           test: /\.(png|jpe?g|gif|svg)$/i,
           type: 'asset/resource',
           generator: {
             filename: 'images/[name].[contenthash][ext]',
           },
           use: [
             {
               loader: 'image-webpack-loader',
               options: {
                 mozjpeg: { progressive: true, quality: 80 },
                 optipng: { enabled: false },
                 pngquant: { quality: [0.6, 0.8] },
                 webp: { quality: 80 },
               },
             },
           ],
         },
       ],
     },
   };
   ```

   **Next.js CDN Configuration:**
   ```javascript
   // next.config.js
   const withOptimizedImages = require('next-optimized-images');

   module.exports = withOptimizedImages({
     assetPrefix: process.env.CDN_URL || '',
     
     images: {
       domains: ['cdn.example.com'],
       formats: ['image/webp', 'image/avif'],
       deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
       imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
       minimumCacheTTL: 31536000, // 1 year
     },
     
     async headers() {
       return [
         {
           source: '/static/(.*)',
           headers: [
             {
               key: 'Cache-Control',
               value: 'public, max-age=31536000, immutable',
             },
           ],
         },
       ];
     },
   });
   ```

4. **Compression and Optimization**
   - Configure optimal compression settings:

   **Gzip/Brotli Compression:**
   ```javascript
   // Express.js compression middleware
   const compression = require('compression');
   const express = require('express');
   const app = express();

   // Advanced compression configuration
   app.use(compression({
     level: 6, // Compression level (1-9)
     threshold: 1024, // Only compress files > 1KB
     filter: (req, res) => {
       // Custom compression filter
       if (req.headers['x-no-compression']) {
         return false;
       }
       
       // Compress text-based content types
       return compression.filter(req, res);
     }
   }));

   // Serve pre-compressed files if available
   app.get('*.js', (req, res, next) => {
     const acceptEncoding = req.get('Accept-Encoding');
     
     if (acceptEncoding && acceptEncoding.includes('br')) {
       req.url = req.url + '.br';
       res.set('Content-Encoding', 'br');
       res.set('Content-Type', 'application/javascript');
     } else if (acceptEncoding && acceptEncoding.includes('gzip')) {
       req.url = req.url + '.gz';
       res.set('Content-Encoding', 'gzip');
       res.set('Content-Type', 'application/javascript');
     }
     
     next();
   });
   ```

   **Build-time Compression:**
   ```javascript
   // compression-plugin.js
   const CompressionPlugin = require('compression-webpack-plugin');
   const BrotliPlugin = require('brotli-webpack-plugin');

   module.exports = {
     plugins: [
       // Gzip compression
       new CompressionPlugin({
         algorithm: 'gzip',
         test: /\.(js|css|html|svg)$/,
         threshold: 8192,
         minRatio: 0.8,
       }),
       
       // Brotli compression
       new BrotliPlugin({
         asset: '[path].br[query]',
         test: /\.(js|css|html|svg)$/,
         threshold: 8192,
         minRatio: 0.8,
       }),
     ],
   };
   ```

5. **Cache Headers and Policies**
   - Configure optimal caching strategies:

   **Smart Cache Headers:**
   ```javascript
   // cache-control.js
   class CacheControlManager {
     static getCacheHeaders(filePath, fileType) {
       const cacheStrategies = {
         // Long-term caching for versioned assets
         versioned: {
           'Cache-Control': 'public, max-age=31536000, immutable',
           'Expires': new Date(Date.now() + 31536000000).toUTCString(),
         },
         
         // Medium-term caching for semi-static content
         semiStatic: {
           'Cache-Control': 'public, max-age=86400, must-revalidate',
           'ETag': this.generateETag(filePath),
         },
         
         // Short-term caching for dynamic content
         dynamic: {
           'Cache-Control': 'public, max-age=300, must-revalidate',
           'ETag': this.generateETag(filePath),
         },
         
         // No caching for sensitive content
         noCache: {
           'Cache-Control': 'no-cache, no-store, must-revalidate',
           'Pragma': 'no-cache',
           'Expires': '0',
         },
       };

       // Determine strategy based on file type and path
       if (filePath.match(/\.(js|css|png|jpg|jpeg|gif|ico|woff2?)$/)) {
         return filePath.includes('[hash]') || filePath.includes('[contenthash]') 
           ? cacheStrategies.versioned 
           : cacheStrategies.semiStatic;
       }
       
       if (filePath.startsWith('/api/')) {
         return cacheStrategies.dynamic;
       }
       
       if (filePath.includes('/admin') || filePath.includes('/auth')) {
         return cacheStrategies.noCache;
       }
       
       return cacheStrategies.semiStatic;
     }

     static generateETag(content) {
       return `"${require('crypto').createHash('md5').update(content).digest('hex')}"`;
     }
   }

   // Express middleware
   app.use((req, res, next) => {
     const headers = CacheControlManager.getCacheHeaders(req.path, req.get('Content-Type'));
     Object.entries(headers).forEach(([key, value]) => {
       res.set(key, value);
     });
     next();
   });
   ```

6. **Image Optimization and Delivery**
   - Implement advanced image optimization:

   **Responsive Image Delivery:**
   ```javascript
   // image-optimization.js
   const sharp = require('sharp');
   const fs = require('fs').promises;

   class ImageOptimizer {
     static async generateResponsiveImages(inputPath, outputDir) {
       const sizes = [
         { width: 320, suffix: 'sm' },
         { width: 640, suffix: 'md' },
         { width: 1024, suffix: 'lg' },
         { width: 1920, suffix: 'xl' },
       ];

       const formats = ['webp', 'jpeg'];
       const results = [];

       for (const size of sizes) {
         for (const format of formats) {
           const outputPath = `${outputDir}/${size.suffix}.${format}`;
           
           await sharp(inputPath)
             .resize(size.width, null, { withoutEnlargement: true })
             .toFormat(format, { quality: 80 })
             .toFile(outputPath);
             
           results.push({
             path: outputPath,
             width: size.width,
             format: format,
           });
         }
       }

       return results;
     }

     static generatePictureElement(imageName, alt, className = '') {
       return `
         <picture class="${className}">
           <source media="(min-width: 1024px)" 
                   srcset="/images/${imageName}-xl.webp" 
                   type="image/webp">
           <source media="(min-width: 1024px)" 
                   srcset="/images/${imageName}-xl.jpeg" 
                   type="image/jpeg">
           <source media="(min-width: 640px)" 
                   srcset="/images/${imageName}-lg.webp" 
                   type="image/webp">
           <source media="(min-width: 640px)" 
                   srcset="/images/${imageName}-lg.jpeg" 
                   type="image/jpeg">
           <source media="(min-width: 320px)" 
                   srcset="/images/${imageName}-md.webp" 
                   type="image/webp">
           <source media="(min-width: 320px)" 
                   srcset="/images/${imageName}-md.jpeg" 
                   type="image/jpeg">
           <img src="/images/${imageName}-sm.jpeg" 
                alt="${alt}" 
                loading="lazy"
                decoding="async">
         </picture>
       `;
     }
   }
   ```

7. **CDN Purging and Cache Invalidation**
   - Implement intelligent cache invalidation:

   **CloudFlare Cache Purging:**
   ```javascript
   // cdn-purge.js
   const cloudflare = require('cloudflare');

   class CDNManager {
     constructor() {
       this.cf = new cloudflare({
         email: process.env.CLOUDFLARE_EMAIL,
         key: process.env.CLOUDFLARE_API_KEY
       });
       this.zoneId = process.env.CLOUDFLARE_ZONE_ID;
     }

     async purgeFiles(files) {
       try {
         const result = await this.cf.zones.purgeCache(this.zoneId, {
           files: files.map(file => `https://example.com${file}`)
         });
         console.log('Cache purged successfully:', result);
         return result;
       } catch (error) {
         console.error('Cache purge failed:', error);
         throw error;
       }
     }

     async purgeByTags(tags) {
       try {
         const result = await this.cf.zones.purgeCache(this.zoneId, {
           tags: tags
         });
         console.log('Cache purged by tags:', result);
         return result;
       } catch (error) {
         console.error('Cache purge by tags failed:', error);
         throw error;
       }
     }

     async purgeEverything() {
       try {
         const result = await this.cf.zones.purgeCache(this.zoneId, {
           purge_everything: true
         });
         console.log('All cache purged:', result);
         return result;
       } catch (error) {
         console.error('Full cache purge failed:', error);
         throw error;
       }
     }
   }

   // Usage in deployment pipeline
   const cdnManager = new CDNManager();

   // Selective purging after deployment
   async function postDeploymentPurge() {
     const filesToPurge = [
       '/static/js/main.*.js',
       '/static/css/main.*.css',
       '/',
       '/index.html'
     ];
     
     await cdnManager.purgeFiles(filesToPurge);
   }
   ```

8. **Performance Monitoring and Analytics**
   - Set up CDN performance monitoring:

   **CDN Performance Tracking:**
   ```javascript
   // cdn-analytics.js
   class CDNAnalytics {
     static async getCDNMetrics() {
       const metrics = {
         cacheHitRatio: await this.getCacheHitRatio(),
         bandwidth: await this.getBandwidthUsage(),
         responseTime: await this.getResponseTimes(),
         errorRate: await this.getErrorRate(),
       };

       return metrics;
     }

     static async getCacheHitRatio() {
       // CloudFlare Analytics API
       const response = await fetch(`https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/analytics/dashboard`, {
         headers: {
           'X-Auth-Email': process.env.CLOUDFLARE_EMAIL,
           'X-Auth-Key': process.env.CLOUDFLARE_API_KEY,
         }
       });

       const data = await response.json();
       return data.result.totals.requests.cached / data.result.totals.requests.all;
     }

     static trackCDNPerformance() {
       // Real User Monitoring for CDN performance
       if (typeof window !== 'undefined') {
         const observer = new PerformanceObserver((list) => {
           for (const entry of list.getEntries()) {
             if (entry.name.includes('cdn.example.com')) {
               // Track CDN resource loading times
               console.log('CDN Resource:', {
                 name: entry.name,
                 duration: entry.duration,
                 transferSize: entry.transferSize,
                 encodedBodySize: entry.encodedBodySize,
               });
               
               // Send to analytics
               this.sendCDNMetric({
                 resource: entry.name,
                 loadTime: entry.duration,
                 cacheStatus: entry.transferSize === 0 ? 'hit' : 'miss',
               });
             }
           }
         });

         observer.observe({ entryTypes: ['resource'] });
       }
     }

     static sendCDNMetric(metric) {
       // Send to your analytics service
       fetch('/api/analytics/cdn', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(metric),
       });
     }
   }
   ```

9. **Security and Access Control**
   - Configure CDN security features:

   **CDN Security Configuration:**
   ```javascript
   // cdn-security.js
   class CDNSecurity {
     static setupSecurityHeaders() {
       return {
         'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
         'X-Content-Type-Options': 'nosniff',
         'X-Frame-Options': 'DENY',
         'X-XSS-Protection': '1; mode=block',
         'Referrer-Policy': 'strict-origin-when-cross-origin',
         'Content-Security-Policy': `
           default-src 'self';
           script-src 'self' 'unsafe-inline' cdn.example.com;
           style-src 'self' 'unsafe-inline' cdn.example.com;
           img-src 'self' data: cdn.example.com;
           font-src 'self' cdn.example.com;
         `.replace(/\s+/g, ' ').trim(),
       };
     }

     static configureHotlinkProtection() {
       // CloudFlare Worker for hotlink protection
       return `
         addEventListener('fetch', event => {
           event.respondWith(handleRequest(event.request));
         });

         async function handleRequest(request) {
           const url = new URL(request.url);
           const referer = request.headers.get('Referer');
           
           // Allow requests from your domain and direct access
           const allowedDomains = ['example.com', 'www.example.com'];
           
           if (!referer || allowedDomains.some(domain => referer.includes(domain))) {
             return fetch(request);
           }
           
           // Block hotlinking
           return new Response('Hotlinking not allowed', { status: 403 });
         }
       `;
     }
   }
   ```

10. **Cost Optimization and Monitoring**
    - Implement CDN cost optimization:

    **Cost Monitoring:**
    ```javascript
    // cdn-cost-optimization.js
    class CDNCostOptimizer {
      static async analyzeUsage() {
        const usage = await this.getCDNUsage();
        const recommendations = [];

        // Analyze bandwidth usage by file type
        if (usage.images > usage.total * 0.6) {
          recommendations.push({
            type: 'image_optimization',
            message: 'Images account for >60% of bandwidth. Consider WebP format and better compression.',
            potential_savings: '20-40%'
          });
        }

        // Analyze cache hit ratio
        if (usage.cacheHitRatio < 0.8) {
          recommendations.push({
            type: 'cache_optimization',
            message: 'Cache hit ratio is below 80%. Review cache headers and TTL settings.',
            potential_savings: '10-25%'
          });
        }

        return recommendations;
      }

      static async optimizeTierUsage() {
        // Move less frequently accessed content to cheaper tiers
        const accessPatterns = await this.getAccessPatterns();
        
        const coldFiles = accessPatterns.filter(file => 
          file.requests_per_day < 10 && file.size > 1024 * 1024 // <10 requests/day, >1MB
        );

        console.log(`Found ${coldFiles.length} files suitable for cold storage`);
        return coldFiles;
      }

      static setupCostAlerts() {
        // Monitor CDN costs and set up alerts
        return {
          daily_bandwidth_alert: '100GB',
          monthly_cost_alert: '$500',
          cache_hit_ratio_alert: '75%',
          error_rate_alert: '5%'
        };
      }
    }

    // Monthly cost analysis
    setInterval(async () => {
      const analysis = await CDNCostOptimizer.analyzeUsage();
      console.log('CDN Cost Analysis:', analysis);
    }, 24 * 60 * 60 * 1000); // Daily
    ```