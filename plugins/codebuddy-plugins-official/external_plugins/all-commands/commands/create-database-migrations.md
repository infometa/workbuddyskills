---
description: Create and manage database migrations
category: database-operations
allowed-tools: Bash(npm *), Edit
---

# Create Database Migrations

Create and manage database migrations

## Instructions

1. **Migration Strategy and Planning**
   - Analyze current database schema and target changes
   - Plan migration strategy for zero-downtime deployments
   - Define rollback procedures and data safety measures
   - Assess migration complexity and potential risks
   - Plan for data transformation and validation

2. **Migration Framework Setup**
   - Set up comprehensive migration framework:

   **Node.js Migration Framework:**
   ```javascript
   // migrations/migration-framework.js
   const fs = require('fs').promises;
   const path = require('path');
   const { Pool } = require('pg');

   class MigrationManager {
     constructor(databaseConfig) {
       this.pool = new Pool(databaseConfig);
       this.migrationsDir = path.join(__dirname, 'migrations');
       this.lockTimeout = 30000; // 30 seconds
     }

     async initialize() {
       // Create migrations tracking table
       await this.pool.query(`
         CREATE TABLE IF NOT EXISTS schema_migrations (
           id SERIAL PRIMARY KEY,
           version VARCHAR(255) UNIQUE NOT NULL,
           name VARCHAR(255) NOT NULL,
           executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
           execution_time_ms INTEGER,
           checksum VARCHAR(64),
           rollback_sql TEXT,
           batch_number INTEGER
         );
         
         CREATE INDEX IF NOT EXISTS idx_schema_migrations_version 
         ON schema_migrations(version);
         
         CREATE INDEX IF NOT EXISTS idx_schema_migrations_batch 
         ON schema_migrations(batch_number);
       `);

       // Create migration lock table
       await this.pool.query(`
         CREATE TABLE IF NOT EXISTS migration_lock (
           id INTEGER PRIMARY KEY DEFAULT 1,
           is_locked BOOLEAN DEFAULT FALSE,
           locked_at TIMESTAMP WITH TIME ZONE,
           locked_by VARCHAR(255),
           CHECK (id = 1)
         );
         
         INSERT INTO migration_lock (id, is_locked) 
         VALUES (1, FALSE) 
         ON CONFLICT (id) DO NOTHING;
       `);
     }

     async acquireLock(lockId = 'migration') {
       const client = await this.pool.connect();
       try {
         const result = await client.query(`
           UPDATE migration_lock 
           SET is_locked = TRUE, locked_at = CURRENT_TIMESTAMP, locked_by = $1
           WHERE id = 1 AND (is_locked = FALSE OR locked_at < CURRENT_TIMESTAMP - INTERVAL '${this.lockTimeout} milliseconds')
           RETURNING is_locked;
         `, [lockId]);

         if (result.rows.length === 0) {
           throw new Error('Could not acquire migration lock - another migration may be running');
         }

         return client;
       } catch (error) {
         client.release();
         throw error;
       }
     }

     async releaseLock(client) {
       try {
         await client.query(`
           UPDATE migration_lock 
           SET is_locked = FALSE, locked_at = NULL, locked_by = NULL 
           WHERE id = 1;
         `);
       } finally {
         client.release();
       }
     }

     async getPendingMigrations() {
       const files = await fs.readdir(this.migrationsDir);
       const migrationFiles = files
         .filter(file => file.endsWith('.sql') || file.endsWith('.js'))
         .sort();

       const executedMigrations = await this.pool.query(
         'SELECT version FROM schema_migrations ORDER BY version'
       );
       const executedVersions = new Set(executedMigrations.rows.map(row => row.version));

       return migrationFiles
         .map(file => {
           const version = this.extractVersion(file);
           return { file, version, executed: executedVersions.has(version) };
         })
         .filter(migration => !migration.executed);
     }

     extractVersion(filename) {
       const match = filename.match(/^(\d{14})/);
       if (!match) {
         throw new Error(`Invalid migration filename format: ${filename}`);
       }
       return match[1];
     }

     async runMigration(migrationFile) {
       const version = this.extractVersion(migrationFile.file);
       const filePath = path.join(this.migrationsDir, migrationFile.file);
       const startTime = Date.now();

       console.log(`Running migration: ${migrationFile.file}`);

       const client = await this.pool.connect();
       try {
         await client.query('BEGIN');

         let migrationContent;
         let rollbackSql = '';

         if (migrationFile.file.endsWith('.js')) {
           // JavaScript migration
           const migration = require(filePath);
           await migration.up(client);
           rollbackSql = migration.down ? migration.down.toString() : '';
         } else {
           // SQL migration
           migrationContent = await fs.readFile(filePath, 'utf8');
           const { upSql, downSql } = this.parseSqlMigration(migrationContent);
           
           await client.query(upSql);
           rollbackSql = downSql;
         }

         const executionTime = Date.now() - startTime;
         const checksum = this.generateChecksum(migrationContent || migrationFile.file);
         const batchNumber = await this.getNextBatchNumber();

         // Record migration execution
         await client.query(`
           INSERT INTO schema_migrations (version, name, execution_time_ms, checksum, rollback_sql, batch_number)
           VALUES ($1, $2, $3, $4, $5, $6)
         `, [version, migrationFile.file, executionTime, checksum, rollbackSql, batchNumber]);

         await client.query('COMMIT');
         console.log(`✓ Migration ${migrationFile.file} completed in ${executionTime}ms`);

       } catch (error) {
         await client.query('ROLLBACK');
         console.error(`✗ Migration ${migrationFile.file} failed:`, error.message);
         throw error;
       } finally {
         client.release();
       }
     }

     parseSqlMigration(content) {
       const lines = content.split('\n');
       let upSql = '';
       let downSql = '';
       let currentSection = 'up';

       for (const line of lines) {
         if (line.trim().startsWith('-- +migrate Down')) {
           currentSection = 'down';
           continue;
         }
         if (line.trim().startsWith('-- +migrate Up')) {
           currentSection = 'up';
           continue;
         }

         if (currentSection === 'up') {
           upSql += line + '\n';
         } else if (currentSection === 'down') {
           downSql += line + '\n';
         }
       }

       return { upSql: upSql.trim(), downSql: downSql.trim() };
     }

     generateChecksum(content) {
       const crypto = require('crypto');
       return crypto.createHash('sha256').update(content).digest('hex');
     }

     async getNextBatchNumber() {
       const result = await this.pool.query(
         'SELECT COALESCE(MAX(batch_number), 0) + 1 as next_batch FROM schema_migrations'
       );
       return result.rows[0].next_batch;
     }

     async migrate() {
       await this.initialize();
       
       const client = await this.acquireLock('migration-runner');
       try {
         const pendingMigrations = await this.getPendingMigrations();
         
         if (pendingMigrations.length === 0) {
           console.log('No pending migrations');
           return;
         }

         console.log(`Found ${pendingMigrations.length} pending migrations`);
         
         for (const migration of pendingMigrations) {
           await this.runMigration(migration);
         }

         console.log('All migrations completed successfully');
       } finally {
         await this.releaseLock(client);
       }
     }

     async rollback(steps = 1) {
       await this.initialize();
       
       const client = await this.acquireLock('migration-rollback');
       try {
         const lastMigrations = await this.pool.query(`
           SELECT * FROM schema_migrations 
           ORDER BY executed_at DESC, version DESC 
           LIMIT $1
         `, [steps]);

         if (lastMigrations.rows.length === 0) {
           console.log('No migrations to rollback');
           return;
         }

         for (const migration of lastMigrations.rows) {
           await this.rollbackMigration(migration);
         }

         console.log(`Rolled back ${lastMigrations.rows.length} migrations`);
       } finally {
         await this.releaseLock(client);
       }
     }

     async rollbackMigration(migration) {
       console.log(`Rolling back migration: ${migration.name}`);
       
       const client = await this.pool.connect();
       try {
         await client.query('BEGIN');

         if (migration.rollback_sql) {
           await client.query(migration.rollback_sql);
         } else {
           console.warn(`No rollback SQL available for ${migration.name}`);
         }

         await client.query(
           'DELETE FROM schema_migrations WHERE version = $1',
           [migration.version]
         );

         await client.query('COMMIT');
         console.log(`✓ Rolled back migration: ${migration.name}`);

       } catch (error) {
         await client.query('ROLLBACK');
         console.error(`✗ Rollback failed for ${migration.name}:`, error.message);
         throw error;
       } finally {
         client.release();
       }
     }
   }

   module.exports = MigrationManager;
   ```

3. **Migration File Templates**
   - Create standardized migration templates:

   **SQL Migration Template:**
   ```sql
   -- +migrate Up
   -- Migration: Add user preferences table
   -- Author: Developer Name
   -- Date: 2024-01-15
   -- Description: Create user_preferences table to store user-specific settings

   CREATE TABLE user_preferences (
     id BIGSERIAL PRIMARY KEY,
     user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     category VARCHAR(100) NOT NULL,
     key VARCHAR(100) NOT NULL,
     value JSONB NOT NULL DEFAULT '{}',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     
     UNIQUE(user_id, category, key)
   );

   -- Add indexes for efficient querying
   CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
   CREATE INDEX idx_user_preferences_category ON user_preferences(category);
   CREATE INDEX idx_user_preferences_key ON user_preferences(key);

   -- Add comments for documentation
   COMMENT ON TABLE user_preferences IS 'User-specific preference settings organized by category';
   COMMENT ON COLUMN user_preferences.category IS 'Preference category (e.g., notifications, display, privacy)';
   COMMENT ON COLUMN user_preferences.key IS 'Specific preference key within the category';
   COMMENT ON COLUMN user_preferences.value IS 'Preference value stored as JSONB for flexibility';

   -- +migrate Down
   -- Rollback: Remove user preferences table

   DROP TABLE IF EXISTS user_preferences CASCADE;
   ```

   **JavaScript Migration Template:**
   ```javascript
   // migrations/20240115120000_add_user_preferences.js
   const migration = {
     name: 'Add user preferences table',
     description: 'Create user_preferences table for storing user-specific settings',
     
     async up(client) {
       console.log('Creating user_preferences table...');
       
       await client.query(`
         CREATE TABLE user_preferences (
           id BIGSERIAL PRIMARY KEY,
           user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
           category VARCHAR(100) NOT NULL,
           key VARCHAR(100) NOT NULL,
           value JSONB NOT NULL DEFAULT '{}',
           created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
           updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
           
           UNIQUE(user_id, category, key)
         );
       `);

       await client.query(`
         CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
       `);

       await client.query(`
         CREATE INDEX idx_user_preferences_category ON user_preferences(category);
       `);

       console.log('✓ user_preferences table created successfully');
     },

     async down(client) {
       console.log('Dropping user_preferences table...');
       
       await client.query('DROP TABLE IF EXISTS user_preferences CASCADE;');
       
       console.log('✓ user_preferences table dropped successfully');
     }
   };

   module.exports = migration;
   ```

4. **Advanced Migration Patterns**
   - Implement complex migration scenarios:

   **Data Migration with Validation:**
   ```javascript
   // migrations/20240115130000_migrate_user_settings.js
   const migration = {
     name: 'Migrate user settings to new format',
     description: 'Transform legacy user_settings JSONB column to normalized user_preferences table',
     
     async up(client) {
       console.log('Starting user settings migration...');
       
       // Step 1: Create temporary backup
       await client.query(`
         CREATE TABLE user_settings_backup AS 
         SELECT * FROM users WHERE settings IS NOT NULL;
       `);
       
       console.log('✓ Created backup of existing user settings');

       // Step 2: Migrate data in batches
       const batchSize = 1000;
       let offset = 0;
       let processedCount = 0;

       while (true) {
         const result = await client.query(`
           SELECT id, settings 
           FROM users 
           WHERE settings IS NOT NULL 
           ORDER BY id 
           LIMIT $1 OFFSET $2
         `, [batchSize, offset]);

         if (result.rows.length === 0) break;

         for (const user of result.rows) {
           await this.migrateUserSettings(client, user.id, user.settings);
           processedCount++;
         }

         offset += batchSize;
         console.log(`✓ Processed ${processedCount} users...`);
       }

       // Step 3: Validate migration
       const validationResult = await this.validateMigration(client);
       if (!validationResult.isValid) {
         throw new Error(`Migration validation failed: ${validationResult.errors.join(', ')}`);
       }

       console.log(`✓ Successfully migrated ${processedCount} user settings`);
     },

     async migrateUserSettings(client, userId, settings) {
       const settingsObj = typeof settings === 'string' ? JSON.parse(settings) : settings;
       
       for (const [category, categorySettings] of Object.entries(settingsObj)) {
         if (typeof categorySettings === 'object') {
           for (const [key, value] of Object.entries(categorySettings)) {
             await client.query(`
               INSERT INTO user_preferences (user_id, category, key, value)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (user_id, category, key) DO UPDATE
               SET value = $4, updated_at = CURRENT_TIMESTAMP
             `, [userId, category, key, JSON.stringify(value)]);
           }
         } else {
           // Handle flat settings structure
           await client.query(`
             INSERT INTO user_preferences (user_id, category, key, value)
             VALUES ($1, $2, $3, $4)
             ON CONFLICT (user_id, category, key) DO UPDATE
             SET value = $4, updated_at = CURRENT_TIMESTAMP
           `, [userId, 'general', category, JSON.stringify(categorySettings)]);
         }
       }
     },

     async validateMigration(client) {
       const errors = [];
       
       // Check for data consistency
       const oldCount = await client.query(
         'SELECT COUNT(*) FROM users WHERE settings IS NOT NULL'
       );
       
       const newCount = await client.query(
         'SELECT COUNT(DISTINCT user_id) FROM user_preferences'
       );

       if (oldCount.rows[0].count !== newCount.rows[0].count) {
         errors.push(`User count mismatch: ${oldCount.rows[0].count} vs ${newCount.rows[0].count}`);
       }

       // Check for required preferences
       const missingPrefs = await client.query(`
         SELECT u.id FROM users u
         LEFT JOIN user_preferences up ON u.id = up.user_id
         WHERE u.settings IS NOT NULL AND up.user_id IS NULL
       `);

       if (missingPrefs.rows.length > 0) {
         errors.push(`${missingPrefs.rows.length} users missing preferences`);
       }

       return {
         isValid: errors.length === 0,
         errors
       };
     },

     async down(client) {
       console.log('Rolling back user settings migration...');
       
       // Restore from backup
       await client.query(`
         UPDATE users 
         SET settings = backup.settings
         FROM user_settings_backup backup
         WHERE users.id = backup.id;
       `);
       
       // Clean up
       await client.query('DELETE FROM user_preferences;');
       await client.query('DROP TABLE user_settings_backup;');
       
       console.log('✓ Rollback completed');
     }
   };

   module.exports = migration;
   ```

5. **Schema Alteration Migrations**
   - Handle schema changes safely:

   **Safe Column Addition:**
   ```sql
   -- +migrate Up
   -- Migration: Add email verification tracking
   -- Safe column addition with default values

   -- Add new columns with safe defaults
   ALTER TABLE users 
   ADD COLUMN email_verification_token VARCHAR(255),
   ADD COLUMN email_verification_expires_at TIMESTAMP WITH TIME ZONE,
   ADD COLUMN email_verification_attempts INTEGER DEFAULT 0;

   -- Add index for token lookup
   CREATE INDEX CONCURRENTLY idx_users_email_verification_token 
   ON users(email_verification_token) 
   WHERE email_verification_token IS NOT NULL;

   -- Add constraint for expiration logic
   ALTER TABLE users 
   ADD CONSTRAINT chk_email_verification_expires 
   CHECK (
     (email_verification_token IS NULL AND email_verification_expires_at IS NULL) OR
     (email_verification_token IS NOT NULL AND email_verification_expires_at IS NOT NULL)
   );

   -- +migrate Down
   -- Remove email verification columns

   DROP INDEX IF EXISTS idx_users_email_verification_token;
   ALTER TABLE users 
   DROP CONSTRAINT IF EXISTS chk_email_verification_expires,
   DROP COLUMN IF EXISTS email_verification_token,
   DROP COLUMN IF EXISTS email_verification_expires_at,
   DROP COLUMN IF EXISTS email_verification_attempts;
   ```

   **Safe Table Restructuring:**
   ```sql
   -- +migrate Up
   -- Migration: Split user addresses into separate table
   -- Zero-downtime table restructuring

   -- Step 1: Create new addresses table
   CREATE TABLE user_addresses (
     id BIGSERIAL PRIMARY KEY,
     user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     type address_type DEFAULT 'shipping',
     first_name VARCHAR(100),
     last_name VARCHAR(100),
     company VARCHAR(255),
     address_line_1 VARCHAR(255) NOT NULL,
     address_line_2 VARCHAR(255),
     city VARCHAR(100) NOT NULL,
     state VARCHAR(100),
     postal_code VARCHAR(20),
     country CHAR(2) NOT NULL DEFAULT 'US',
     phone VARCHAR(20),
     is_default BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   CREATE TYPE address_type AS ENUM ('billing', 'shipping');

   -- Add indexes
   CREATE INDEX idx_user_addresses_user_id ON user_addresses(user_id);
   CREATE INDEX idx_user_addresses_type ON user_addresses(type);
   CREATE UNIQUE INDEX idx_user_addresses_default 
   ON user_addresses(user_id, type) 
   WHERE is_default = TRUE;

   -- Step 2: Migrate existing address data
   INSERT INTO user_addresses (
     user_id, type, first_name, last_name, address_line_1, 
     city, state, postal_code, country, is_default
   )
   SELECT 
     id, 'shipping', first_name, last_name, address,
     city, state, postal_code, 
     COALESCE(country, 'US'), TRUE
   FROM users 
   WHERE address IS NOT NULL;

   -- Step 3: Create view for backward compatibility
   CREATE VIEW users_with_address AS
   SELECT 
     u.*,
     ua.address_line_1 as address,
     ua.city,
     ua.state,
     ua.postal_code,
     ua.country
   FROM users u
   LEFT JOIN user_addresses ua ON u.id = ua.user_id AND ua.is_default = TRUE AND ua.type = 'shipping';

   -- Step 4: Add trigger to maintain view consistency
   CREATE OR REPLACE FUNCTION sync_user_address()
   RETURNS TRIGGER AS $$
   BEGIN
     IF TG_OP = 'UPDATE' THEN
       -- Update default shipping address
       UPDATE user_addresses 
       SET 
         address_line_1 = NEW.address,
         city = NEW.city,
         state = NEW.state,
         postal_code = NEW.postal_code,
         country = NEW.country,
         updated_at = CURRENT_TIMESTAMP
       WHERE user_id = NEW.id AND type = 'shipping' AND is_default = TRUE;
       
       RETURN NEW;
     END IF;
     RETURN NULL;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER trigger_sync_user_address
   AFTER UPDATE ON users
   FOR EACH ROW
   WHEN (OLD.address IS DISTINCT FROM NEW.address OR 
         OLD.city IS DISTINCT FROM NEW.city OR
         OLD.state IS DISTINCT FROM NEW.state OR
         OLD.postal_code IS DISTINCT FROM NEW.postal_code OR
         OLD.country IS DISTINCT FROM NEW.country)
   EXECUTE FUNCTION sync_user_address();

   -- +migrate Down
   -- Restore original structure

   DROP TRIGGER IF EXISTS trigger_sync_user_address ON users;
   DROP FUNCTION IF EXISTS sync_user_address();
   DROP VIEW IF EXISTS users_with_address;
   DROP TABLE IF EXISTS user_addresses CASCADE;
   DROP TYPE IF EXISTS address_type;
   ```

6. **Migration Testing Framework**
   - Test migrations thoroughly:

   **Migration Test Suite:**
   ```javascript
   // tests/migration-tests.js
   const { Pool } = require('pg');
   const MigrationManager = require('../migrations/migration-framework');

   class MigrationTester {
     constructor() {
       this.testDbConfig = {
         host: process.env.TEST_DB_HOST || 'localhost',
         port: process.env.TEST_DB_PORT || 5432,
         database: process.env.TEST_DB_NAME || 'test_db',
         user: process.env.TEST_DB_USER || 'postgres',
         password: process.env.TEST_DB_PASSWORD || 'password'
       };
       
       this.pool = new Pool(this.testDbConfig);
       this.migrationManager = new MigrationManager(this.testDbConfig);
     }

     async setupTestDatabase() {
       // Create fresh test database
       const adminPool = new Pool({
         ...this.testDbConfig,
         database: 'postgres'
       });

       try {
         await adminPool.query(`DROP DATABASE IF EXISTS ${this.testDbConfig.database}`);
         await adminPool.query(`CREATE DATABASE ${this.testDbConfig.database}`);
         console.log('✓ Test database created');
       } finally {
         await adminPool.end();
       }
     }

     async teardownTestDatabase() {
       await this.pool.end();
       
       const adminPool = new Pool({
         ...this.testDbConfig,
         database: 'postgres'
       });

       try {
         await adminPool.query(`DROP DATABASE IF EXISTS ${this.testDbConfig.database}`);
         console.log('✓ Test database cleaned up');
       } finally {
         await adminPool.end();
       }
     }

     async testMigrationUpDown(migrationFile) {
       console.log(`Testing migration: ${migrationFile}`);
       
       try {
         // Test migration up
         const startTime = Date.now();
         await this.migrationManager.runMigration({ file: migrationFile });
         const upTime = Date.now() - startTime;
         
         console.log(`✓ Migration up completed in ${upTime}ms`);

         // Verify migration was recorded
         const migrationRecord = await this.pool.query(
           'SELECT * FROM schema_migrations WHERE name = $1',
           [migrationFile]
         );
         
         if (migrationRecord.rows.length === 0) {
           throw new Error('Migration not recorded in schema_migrations table');
         }

         // Test migration down
         const rollbackStartTime = Date.now();
         await this.migrationManager.rollbackMigration(migrationRecord.rows[0]);
         const downTime = Date.now() - rollbackStartTime;
         
         console.log(`✓ Migration down completed in ${downTime}ms`);

         // Verify migration was removed
         const afterRollback = await this.pool.query(
           'SELECT * FROM schema_migrations WHERE name = $1',
           [migrationFile]
         );
         
         if (afterRollback.rows.length > 0) {
           throw new Error('Migration not removed after rollback');
         }

         return {
           success: true,
           upTime,
           downTime,
           migrationFile
         };

       } catch (error) {
         console.error(`✗ Migration test failed: ${error.message}`);
         return {
           success: false,
           error: error.message,
           migrationFile
         };
       }
     }

     async testDataIntegrity(testData) {
       console.log('Testing data integrity...');
       
       // Insert test data
       const insertResults = [];
       for (const table of Object.keys(testData)) {
         for (const record of testData[table]) {
           try {
             const columns = Object.keys(record);
             const values = Object.values(record);
             const placeholders = values.map((_, i) => `$${i + 1}`).join(', ');
             
             const result = await this.pool.query(
               `INSERT INTO ${table} (${columns.join(', ')}) VALUES (${placeholders}) RETURNING id`,
               values
             );
             
             insertResults.push({
               table,
               id: result.rows[0].id,
               success: true
             });
           } catch (error) {
             insertResults.push({
               table,
               success: false,
               error: error.message
             });
           }
         }
       }

       return insertResults;
     }

     async testPerformance(queries) {
       console.log('Testing query performance...');
       
       const performanceResults = [];
       
       for (const query of queries) {
         const startTime = process.hrtime.bigint();
         
         try {
           const result = await this.pool.query(query.sql, query.params || []);
           const endTime = process.hrtime.bigint();
           const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds
           
           performanceResults.push({
             name: query.name,
             duration,
             rowCount: result.rows.length,
             success: true
           });
           
           if (duration > (query.maxDuration || 1000)) {
             console.warn(`⚠ Query ${query.name} took ${duration}ms (expected < ${query.maxDuration || 1000}ms)`);
           }
           
         } catch (error) {
           performanceResults.push({
             name: query.name,
             success: false,
             error: error.message
           });
         }
       }

       return performanceResults;
     }

     async runFullTestSuite() {
       console.log('Starting migration test suite...');
       
       await this.setupTestDatabase();
       await this.migrationManager.initialize();
       
       try {
         const testResults = {
           migrations: [],
           dataIntegrity: [],
           performance: [],
           summary: { passed: 0, failed: 0 }
         };

         // Test all migration files
         const migrationFiles = await this.migrationManager.getPendingMigrations();
         
         for (const migration of migrationFiles) {
           const result = await this.testMigrationUpDown(migration.file);
           testResults.migrations.push(result);
           
           if (result.success) {
             testResults.summary.passed++;
           } else {
             testResults.summary.failed++;
           }
         }

         console.log('\n📊 Test Results Summary:');
         console.log(`✓ Passed: ${testResults.summary.passed}`);
         console.log(`✗ Failed: ${testResults.summary.failed}`);
         console.log(`📈 Success Rate: ${(testResults.summary.passed / (testResults.summary.passed + testResults.summary.failed) * 100).toFixed(1)}%`);

         return testResults;

       } finally {
         await this.teardownTestDatabase();
       }
     }
   }

   module.exports = MigrationTester;

   // CLI usage
   if (require.main === module) {
     const tester = new MigrationTester();
     tester.runFullTestSuite()
       .then(results => {
         console.log('\nTest suite completed');
         process.exit(results.summary.failed > 0 ? 1 : 0);
       })
       .catch(error => {
         console.error('Test suite failed:', error);
         process.exit(1);
       });
   }
   ```

7. **Production Migration Safety**
   - Implement production-safe migration practices:

   **Safe Production Migration:**
   ```javascript
   // migrations/production-safety.js
   class ProductionMigrationSafety {
     static async validateProductionMigration(migrationFile, pool) {
       const safety = new ProductionMigrationSafety(pool);
       
       const checks = [
         safety.checkTableLocks.bind(safety),
         safety.checkDataSize.bind(safety),
         safety.checkDependencies.bind(safety),
         safety.checkBackupStatus.bind(safety),
         safety.checkMaintenanceWindow.bind(safety)
       ];

       const results = [];
       for (const check of checks) {
         const result = await check(migrationFile);
         results.push(result);
         
         if (!result.passed && result.blocking) {
           throw new Error(`Migration blocked: ${result.message}`);
         }
       }

       return results;
     }

     constructor(pool) {
       this.pool = pool;
     }

     async checkTableLocks(migrationFile) {
       // Check for long-running transactions that might block migration
       const longTransactions = await this.pool.query(`
         SELECT 
           pid,
           now() - pg_stat_activity.query_start AS duration,
           query,
           state
         FROM pg_stat_activity 
         WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
         AND state IN ('active', 'idle in transaction');
       `);

       return {
         name: 'table_locks',
         passed: longTransactions.rows.length === 0,
         blocking: true,
         message: longTransactions.rows.length > 0 
           ? `${longTransactions.rows.length} long-running transactions detected`
           : 'No blocking transactions found',
         details: longTransactions.rows
       };
     }

     async checkDataSize(migrationFile) {
       // Estimate migration impact based on data size
       const tableSizes = await this.pool.query(`
         SELECT 
           schemaname,
           tablename,
           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
           pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
         FROM pg_tables 
         WHERE schemaname = 'public'
         ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
       `);

       const largeTables = tableSizes.rows.filter(table => table.size_bytes > 1000000000); // > 1GB

       return {
         name: 'data_size',
         passed: largeTables.length < 5,
         blocking: false,
         message: `${largeTables.length} tables > 1GB found`,
         details: largeTables
       };
     }

     async checkDependencies(migrationFile) {
       // Check for dependent applications or services
       const activeConnections = await this.pool.query(`
         SELECT 
           application_name,
           COUNT(*) as connection_count,
           COUNT(*) FILTER (WHERE state = 'active') as active_count
         FROM pg_stat_activity 
         WHERE datname = current_database()
         AND application_name IS NOT NULL
         GROUP BY application_name
         ORDER BY connection_count DESC;
       `);

       const highUsage = activeConnections.rows.filter(app => app.active_count > 10);

       return {
         name: 'dependencies',
         passed: highUsage.length === 0,
         blocking: false,
         message: highUsage.length > 0 
           ? `${highUsage.length} applications with high database usage`
           : 'Database usage within acceptable limits',
         details: activeConnections.rows
       };
     }

     async checkBackupStatus(migrationFile) {
       // Verify recent backup exists
       const lastBackup = await this.pool.query(`
         SELECT 
           pg_last_wal_receive_lsn(),
           pg_last_wal_replay_lsn(),
           EXTRACT(EPOCH FROM (now() - pg_stat_file('base/backup_label', true).modification))::int as backup_age_seconds
         WHERE pg_stat_file('base/backup_label', true) IS NOT NULL;
       `);

       const backupExists = lastBackup.rows.length > 0;
       const backupAge = backupExists ? lastBackup.rows[0].backup_age_seconds : null;
       const isRecentBackup = backupAge !== null && backupAge < 86400; // 24 hours

       return {
         name: 'backup_status',
         passed: isRecentBackup,
         blocking: true,
         message: isRecentBackup 
           ? `Recent backup available (${Math.round(backupAge / 3600)} hours old)`
           : 'No recent backup found - backup required before migration',
         details: { backupExists, backupAge }
       };
     }

     async checkMaintenanceWindow(migrationFile) {
       // Check if we're in approved maintenance window
       const now = new Date();
       const hour = now.getUTCHours();
       const dayOfWeek = now.getUTCDay();
       
       // Define maintenance windows (UTC)
       const maintenanceWindows = [
         { days: [0, 6], startHour: 2, endHour: 6 }, // Weekend early morning
         { days: [1, 2, 3, 4, 5], startHour: 3, endHour: 5 } // Weekday early morning
       ];

       const inMaintenanceWindow = maintenanceWindows.some(window => 
         window.days.includes(dayOfWeek) && 
         hour >= window.startHour && 
         hour < window.endHour
       );

       return {
         name: 'maintenance_window',
         passed: inMaintenanceWindow,
         blocking: false,
         message: inMaintenanceWindow 
           ? 'Currently in maintenance window'
           : `Outside maintenance window (current UTC hour: ${hour})`,
         details: { currentHour: hour, dayOfWeek, maintenanceWindows }
       };
     }
   }

   module.exports = ProductionMigrationSafety;
   ```

8. **Migration Monitoring and Alerting**
   - Monitor migration execution:

   **Migration Monitoring:**
   ```javascript
   // migrations/migration-monitor.js
   class MigrationMonitor {
     constructor(alertService) {
       this.alertService = alertService;
       this.metrics = {
         executionTimes: [],
         errorCounts: {},
         successCounts: {}
       };
     }

     async monitorMigration(migrationName, migrationFn) {
       const startTime = Date.now();
       const memoryBefore = process.memoryUsage();
       
       try {
         console.log(`🚀 Starting migration: ${migrationName}`);
         
         const result = await migrationFn();
         
         const endTime = Date.now();
         const duration = endTime - startTime;
         const memoryAfter = process.memoryUsage();
         
         // Record success metrics
         this.recordSuccess(migrationName, duration, memoryAfter.heapUsed - memoryBefore.heapUsed);
         
         // Alert on long-running migrations
         if (duration > 300000) { // 5 minutes
           await this.alertService.sendAlert({
             type: 'warning',
             title: 'Long-running migration',
             message: `Migration ${migrationName} took ${duration}ms to complete`,
             severity: duration > 600000 ? 'high' : 'medium'
           });
         }

         console.log(`✅ Migration completed: ${migrationName} (${duration}ms)`);
         return result;

       } catch (error) {
         const duration = Date.now() - startTime;
         
         // Record error metrics
         this.recordError(migrationName, error, duration);
         
         // Send error alert
         await this.alertService.sendAlert({
           type: 'error',
           title: 'Migration failed',
           message: `Migration ${migrationName} failed: ${error.message}`,
           severity: 'critical',
           details: {
             migrationName,
             duration,
             error: error.message,
             stack: error.stack
           }
         });

         console.error(`❌ Migration failed: ${migrationName}`, error);
         throw error;
       }
     }

     recordSuccess(migrationName, duration, memoryDelta) {
       this.metrics.executionTimes.push({
         migration: migrationName,
         duration,
         memoryDelta,
         timestamp: new Date()
       });
       
       this.metrics.successCounts[migrationName] = 
         (this.metrics.successCounts[migrationName] || 0) + 1;
     }

     recordError(migrationName, error, duration) {
       this.metrics.errorCounts[migrationName] = 
         (this.metrics.errorCounts[migrationName] || 0) + 1;

       // Log detailed error information
       console.error('Migration Error Details:', {
         migration: migrationName,
         duration,
         error: error.message,
         stack: error.stack,
         timestamp: new Date()
       });
     }

     getMetrics() {
       return {
         averageExecutionTime: this.calculateAverageExecutionTime(),
         totalMigrations: this.metrics.executionTimes.length,
         successRate: this.calculateSuccessRate(),
         errorCounts: this.metrics.errorCounts,
         recentMigrations: this.metrics.executionTimes.slice(-10)
       };
     }

     calculateAverageExecutionTime() {
       if (this.metrics.executionTimes.length === 0) return 0;
       
       const total = this.metrics.executionTimes.reduce((sum, record) => sum + record.duration, 0);
       return Math.round(total / this.metrics.executionTimes.length);
     }

     calculateSuccessRate() {
       const totalSuccess = Object.values(this.metrics.successCounts).reduce((sum, count) => sum + count, 0);
       const totalErrors = Object.values(this.metrics.errorCounts).reduce((sum, count) => sum + count, 0);
       const total = totalSuccess + totalErrors;
       
       return total > 0 ? (totalSuccess / total * 100).toFixed(2) : 100;
     }
   }

   module.exports = MigrationMonitor;
   ```

9. **Migration CLI Tools**
   - Create comprehensive CLI interface:

   **Migration CLI:**
   ```javascript
   #!/usr/bin/env node
   // bin/migrate.js
   const yargs = require('yargs');
   const MigrationManager = require('../migrations/migration-framework');
   const MigrationTester = require('../tests/migration-tests');
   const MigrationMonitor = require('../migrations/migration-monitor');

   const dbConfig = {
     host: process.env.DB_HOST || 'localhost',
     port: process.env.DB_PORT || 5432,
     database: process.env.DB_NAME || 'myapp',
     user: process.env.DB_USER || 'postgres',
     password: process.env.DB_PASSWORD
   };

   const migrationManager = new MigrationManager(dbConfig);

   yargs
     .command('up', 'Run pending migrations', {}, async () => {
       try {
         await migrationManager.migrate();
         console.log('✅ Migrations completed successfully');
         process.exit(0);
       } catch (error) {
         console.error('❌ Migration failed:', error.message);
         process.exit(1);
       }
     })
     .command('down [steps]', 'Rollback migrations', {
       steps: {
         describe: 'Number of migrations to rollback',
         type: 'number',
         default: 1
       }
     }, async (argv) => {
       try {
         await migrationManager.rollback(argv.steps);
         console.log(`✅ Rolled back ${argv.steps} migration(s)`);
         process.exit(0);
       } catch (error) {
         console.error('❌ Rollback failed:', error.message);
         process.exit(1);
       }
     })
     .command('status', 'Show migration status', {}, async () => {
       try {
         const pending = await migrationManager.getPendingMigrations();
         const executed = await migrationManager.pool.query(
           'SELECT version, name, executed_at FROM schema_migrations ORDER BY executed_at DESC'
         );

         console.log('\n📊 Migration Status:');
         console.log(`✅ Executed: ${executed.rows.length}`);
         console.log(`⏳ Pending: ${pending.length}`);
         
         if (pending.length > 0) {
           console.log('\n⏳ Pending Migrations:');
           pending.forEach(m => console.log(`  - ${m.file}`));
         }
         
         if (executed.rows.length > 0) {
           console.log('\n✅ Recent Migrations:');
           executed.rows.slice(0, 5).forEach(m => 
             console.log(`  - ${m.name} (${m.executed_at.toISOString()})`)
           );
         }
         
         process.exit(0);
       } catch (error) {
         console.error('❌ Status check failed:', error.message);
         process.exit(1);
       }
     })
     .command('test', 'Test migrations', {}, async () => {
       try {
         const tester = new MigrationTester();
         const results = await tester.runFullTestSuite();
         
         if (results.summary.failed > 0) {
           console.error(`❌ ${results.summary.failed} migration tests failed`);
           process.exit(1);
         } else {
           console.log(`✅ All ${results.summary.passed} migration tests passed`);
           process.exit(0);
         }
       } catch (error) {
         console.error('❌ Migration testing failed:', error.message);
         process.exit(1);
       }
     })
     .command('create <name>', 'Create new migration file', {
       name: {
         describe: 'Migration name',
         type: 'string',
         demandOption: true
       }
     }, async (argv) => {
       try {
         const timestamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
         const filename = `${timestamp}_${argv.name.replace(/[^a-zA-Z0-9]/g, '_')}.sql`;
         const filepath = path.join(__dirname, '../migrations', filename);
         
         const template = `-- +migrate Up
-- Migration: ${argv.name}
-- Author: ${process.env.USER || 'Unknown'}
-- Date: ${new Date().toISOString().split('T')[0]}
-- Description: [Add description here]

-- Add your migration SQL here

-- +migrate Down
-- Rollback: ${argv.name}

-- Add your rollback SQL here
`;

         await fs.writeFile(filepath, template);
         console.log(`✅ Created migration file: ${filename}`);
         console.log(`📝 Edit the file at: ${filepath}`);
         process.exit(0);
       } catch (error) {
         console.error('❌ Failed to create migration:', error.message);
         process.exit(1);
       }
     })
     .demandCommand()
     .help()
     .argv;
   ```

10. **Production Deployment Integration**
    - Integrate with deployment pipelines:

    **CI/CD Integration:**
    ```yaml
    # .github/workflows/database-migration.yml
    name: Database Migration

    on:
      push:
        branches: [main]
        paths: ['migrations/**']
      
    jobs:
      test-migrations:
        runs-on: ubuntu-latest
        services:
          postgres:
            image: postgres:13
            env:
              POSTGRES_PASSWORD: postgres
              POSTGRES_DB: test_db
            options: >-
              --health-cmd pg_isready
              --health-interval 10s
              --health-timeout 5s
              --health-retries 5

        steps:
          - uses: actions/checkout@v2
          
          - name: Setup Node.js
            uses: actions/setup-node@v2
            with:
              node-version: '16'
              
          - name: Install dependencies
            run: npm ci
            
          - name: Test migrations
            env:
              TEST_DB_HOST: localhost
              TEST_DB_PORT: 5432
              TEST_DB_NAME: test_db
              TEST_DB_USER: postgres
              TEST_DB_PASSWORD: postgres
            run: npm run migrate:test
            
          - name: Check migration safety
            run: npm run migrate:safety-check
            
      deploy-migrations:
        needs: test-migrations
        runs-on: ubuntu-latest
        if: github.ref == 'refs/heads/main'
        
        steps:
          - uses: actions/checkout@v2
          
          - name: Setup Node.js
            uses: actions/setup-node@v2
            with:
              node-version: '16'
              
          - name: Install dependencies
            run: npm ci
            
          - name: Run production migrations
            env:
              DB_HOST: ${{ secrets.PROD_DB_HOST }}
              DB_PORT: ${{ secrets.PROD_DB_PORT }}
              DB_NAME: ${{ secrets.PROD_DB_NAME }}
              DB_USER: ${{ secrets.PROD_DB_USER }}
              DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
            run: |
              npm run migrate:production:safety-check
              npm run migrate:up
              
          - name: Verify deployment
            env:
              DB_HOST: ${{ secrets.PROD_DB_HOST }}
              DB_PORT: ${{ secrets.PROD_DB_PORT }}
              DB_NAME: ${{ secrets.PROD_DB_NAME }}
              DB_USER: ${{ secrets.PROD_DB_USER }}
              DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
            run: npm run migrate:verify
    ```