---
description: Reduce and optimize bundle sizes
category: performance-optimization
allowed-tools: Bash(npm *)
---

# Optimize Bundle Size

Reduce and optimize bundle sizes

## Instructions

1. **Bundle Analysis and Assessment**
   - Analyze current bundle size and composition using webpack-bundle-analyzer or similar
   - Identify large dependencies and unused code
   - Assess current build configuration and optimization settings
   - Create baseline measurements for optimization tracking
   - Document current performance metrics and loading times

2. **Build Tool Configuration**
   - Configure build tool optimization settings:

   **Webpack Configuration:**
   ```javascript
   // webpack.config.js
   const path = require('path');
   const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

   module.exports = {
     mode: 'production',
     optimization: {
       splitChunks: {
         chunks: 'all',
         cacheGroups: {
           vendor: {
             test: /[\\/]node_modules[\\/]/,
             name: 'vendors',
             priority: 10,
             reuseExistingChunk: true,
           },
           common: {
             name: 'common',
             minChunks: 2,
             priority: 5,
             reuseExistingChunk: true,
           },
         },
       },
       usedExports: true,
       sideEffects: false,
     },
     plugins: [
       new BundleAnalyzerPlugin({
         analyzerMode: 'static',
         openAnalyzer: false,
       }),
     ],
   };
   ```

   **Vite Configuration:**
   ```javascript
   // vite.config.js
   import { defineConfig } from 'vite';
   import { visualizer } from 'rollup-plugin-visualizer';

   export default defineConfig({
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             vendor: ['react', 'react-dom'],
             ui: ['@mui/material', '@emotion/react'],
           },
         },
       },
     },
     plugins: [
       visualizer({
         filename: 'dist/stats.html',
         open: true,
         gzipSize: true,
       }),
     ],
   });
   ```

3. **Code Splitting and Lazy Loading**
   - Implement route-based code splitting:

   **React Route Splitting:**
   ```javascript
   import { lazy, Suspense } from 'react';
   import { Routes, Route } from 'react-router-dom';

   const Home = lazy(() => import('./pages/Home'));
   const Dashboard = lazy(() => import('./pages/Dashboard'));
   const Profile = lazy(() => import('./pages/Profile'));

   function App() {
     return (
       <Suspense fallback={<div>Loading...</div>}>
         <Routes>
           <Route path="/" element={<Home />} />
           <Route path="/dashboard" element={<Dashboard />} />
           <Route path="/profile" element={<Profile />} />
         </Routes>
       </Suspense>
     );
   }
   ```

   **Dynamic Imports:**
   ```javascript
   // Lazy load heavy components
   const HeavyComponent = lazy(() => 
     import('./HeavyComponent').then(module => ({
       default: module.HeavyComponent
     }))
   );

   // Conditional loading
   async function loadAnalytics() {
     if (process.env.NODE_ENV === 'production') {
       const { analytics } = await import('./analytics');
       return analytics;
     }
   }
   ```

4. **Tree Shaking and Dead Code Elimination**
   - Configure tree shaking for optimal dead code elimination:

   **Package.json Configuration:**
   ```json
   {
     "sideEffects": false,
     "exports": {
       ".": {
         "import": "./dist/index.esm.js",
         "require": "./dist/index.cjs.js"
       }
     }
   }
   ```

   **Import Optimization:**
   ```javascript
   // Instead of importing entire library
   // import * as _ from 'lodash';

   // Import only what you need
   import debounce from 'lodash/debounce';
   import throttle from 'lodash/throttle';

   // Use babel-plugin-import for automatic optimization
   // .babelrc
   {
     "plugins": [
       ["import", {
         "libraryName": "lodash",
         "libraryDirectory": "",
         "camel2DashComponentName": false
       }, "lodash"]
     ]
   }
   ```

5. **Dependency Optimization**
   - Analyze and optimize dependencies:

   **Package Analysis Script:**
   ```javascript
   // scripts/analyze-deps.js
   const fs = require('fs');
   const path = require('path');

   function analyzeDependencies() {
     const packageJson = JSON.parse(
       fs.readFileSync('package.json', 'utf8')
     );
     
     const deps = {
       ...packageJson.dependencies,
       ...packageJson.devDependencies
     };

     console.log('Large dependencies to review:');
     Object.keys(deps).forEach(dep => {
       try {
         const depPath = require.resolve(dep);
         const stats = fs.statSync(depPath);
         if (stats.size > 100000) { // > 100KB
           console.log(`${dep}: ${(stats.size / 1024).toFixed(2)}KB`);
         }
       } catch (e) {
         // Skip if can't resolve
       }
     });
   }

   analyzeDependencies();
   ```

6. **Asset Optimization**
   - Optimize static assets and media files:

   **Image Optimization:**
   ```javascript
   // webpack.config.js
   module.exports = {
     module: {
       rules: [
         {
           test: /\.(png|jpe?g|gif|svg)$/i,
           use: [
             {
               loader: 'file-loader',
               options: {
                 outputPath: 'images',
               },
             },
             {
               loader: 'image-webpack-loader',
               options: {
                 mozjpeg: { progressive: true, quality: 80 },
                 optipng: { enabled: false },
                 pngquant: { quality: [0.6, 0.8] },
                 gifsicle: { interlaced: false },
               },
             },
           ],
         },
       ],
     },
   };
   ```

7. **Module Federation and Micro-frontends**
   - Implement module federation for large applications:

   **Module Federation Setup:**
   ```javascript
   // webpack.config.js
   const ModuleFederationPlugin = require('@module-federation/webpack');

   module.exports = {
     plugins: [
       new ModuleFederationPlugin({
         name: 'host',
         remotes: {
           mfe1: 'mfe1@http://localhost:3001/remoteEntry.js',
           mfe2: 'mfe2@http://localhost:3002/remoteEntry.js',
         },
         shared: {
           react: { singleton: true },
           'react-dom': { singleton: true },
         },
       }),
     ],
   };
   ```

8. **Performance Monitoring and Measurement**
   - Set up bundle size monitoring:

   **Bundle Size Monitoring:**
   ```javascript
   // scripts/bundle-monitor.js
   const fs = require('fs');
   const path = require('path');
   const gzipSize = require('gzip-size');

   async function measureBundleSize() {
     const distPath = path.join(__dirname, '../dist');
     const files = fs.readdirSync(distPath);
     
     for (const file of files) {
       if (file.endsWith('.js')) {
         const filePath = path.join(distPath, file);
         const content = fs.readFileSync(filePath);
         const originalSize = content.length;
         const compressed = await gzipSize(content);
         
         console.log(`${file}:`);
         console.log(`  Original: ${(originalSize / 1024).toFixed(2)}KB`);
         console.log(`  Gzipped: ${(compressed / 1024).toFixed(2)}KB`);
       }
     }
   }

   measureBundleSize();
   ```

9. **Progressive Loading Strategies**
   - Implement progressive loading and resource hints:

   **Resource Hints:**
   ```html
   <!-- Preload critical resources -->
   <link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
   <link rel="preload" href="/critical.css" as="style">

   <!-- Prefetch non-critical resources -->
   <link rel="prefetch" href="/dashboard.js">
   <link rel="prefetch" href="/profile.js">

   <!-- DNS prefetch for external domains -->
   <link rel="dns-prefetch" href="//api.example.com">
   ```

   **Intersection Observer for Lazy Loading:**
   ```javascript
   // utils/lazyLoad.js
   export function lazyLoadComponent(importFunc) {
     return lazy(() => {
       return new Promise(resolve => {
         const observer = new IntersectionObserver((entries) => {
           entries.forEach(entry => {
             if (entry.isIntersecting) {
               importFunc().then(resolve);
               observer.disconnect();
             }
           });
         });
         
         // Observe a trigger element
         const trigger = document.getElementById('lazy-trigger');
         if (trigger) observer.observe(trigger);
       });
     });
   }
   ```

10. **Validation and Continuous Monitoring**
    - Set up automated bundle size validation:

    **CI/CD Bundle Size Check:**
    ```yaml
    # .github/workflows/bundle-size.yml
    name: Bundle Size Check
    on: [pull_request]

    jobs:
      bundle-size:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v2
          - name: Setup Node
            uses: actions/setup-node@v2
            with:
              node-version: '16'
          - name: Install dependencies
            run: npm ci
          - name: Build bundle
            run: npm run build
          - name: Check bundle size
            run: |
              npm run bundle:analyze
              node scripts/bundle-size-check.js
    ```

    **Bundle Size Threshold Check:**
    ```javascript
    // scripts/bundle-size-check.js
    const fs = require('fs');
    const path = require('path');

    const THRESHOLDS = {
      'main.js': 250 * 1024, // 250KB
      'vendor.js': 500 * 1024, // 500KB
    };

    function checkBundleSize() {
      const distPath = path.join(__dirname, '../dist');
      const files = fs.readdirSync(distPath);
      let failed = false;

      files.forEach(file => {
        if (file.endsWith('.js') && THRESHOLDS[file]) {
          const filePath = path.join(distPath, file);
          const size = fs.statSync(filePath).size;
          
          if (size > THRESHOLDS[file]) {
            console.error(`❌ ${file} exceeds threshold: ${size} > ${THRESHOLDS[file]}`);
            failed = true;
          } else {
            console.log(`✅ ${file} within threshold: ${size}`);
          }
        }
      });

      if (failed) {
        process.exit(1);
      }
    }

    checkBundleSize();
    ```