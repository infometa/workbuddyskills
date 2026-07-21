---
description: Design optimized database schemas
category: database-operations
---

# Design Database Schema

Design optimized database schemas

## Instructions

1. **Requirements Analysis and Data Modeling**
   - Analyze business requirements and data relationships
   - Identify entities, attributes, and relationships
   - Define data types, constraints, and validation rules
   - Plan for scalability and future requirements
   - Consider data access patterns and query requirements

2. **Entity Relationship Design**
   - Create comprehensive entity relationship diagrams:

   **User Management Schema:**
   ```sql
   -- Users table with proper indexing and constraints
   CREATE TABLE users (
     id BIGSERIAL PRIMARY KEY,
     email VARCHAR(255) UNIQUE NOT NULL,
     username VARCHAR(50) UNIQUE NOT NULL,
     password_hash VARCHAR(255) NOT NULL,
     first_name VARCHAR(100) NOT NULL,
     last_name VARCHAR(100) NOT NULL,
     phone VARCHAR(20),
     date_of_birth DATE,
     email_verified BOOLEAN DEFAULT FALSE,
     phone_verified BOOLEAN DEFAULT FALSE,
     status user_status DEFAULT 'active',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     last_login_at TIMESTAMP WITH TIME ZONE,
     deleted_at TIMESTAMP WITH TIME ZONE,
     
     -- Constraints
     CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
     CONSTRAINT users_username_format CHECK (username ~* '^[a-zA-Z0-9_]{3,50}$'),
     CONSTRAINT users_names_not_empty CHECK (LENGTH(TRIM(first_name)) > 0 AND LENGTH(TRIM(last_name)) > 0)
   );

   -- User status enum
   CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending_verification');

   -- User profiles table for extended information
   CREATE TABLE user_profiles (
     user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
     avatar_url VARCHAR(500),
     bio TEXT,
     website VARCHAR(255),
     location VARCHAR(255),
     timezone VARCHAR(50) DEFAULT 'UTC',
     language VARCHAR(10) DEFAULT 'en',
     notification_preferences JSONB DEFAULT '{}',
     privacy_settings JSONB DEFAULT '{}',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   -- User roles and permissions
   CREATE TABLE roles (
     id SERIAL PRIMARY KEY,
     name VARCHAR(50) UNIQUE NOT NULL,
     description TEXT,
     permissions JSONB DEFAULT '[]',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   CREATE TABLE user_roles (
     user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
     role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
     assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     assigned_by BIGINT REFERENCES users(id),
     PRIMARY KEY (user_id, role_id)
   );
   ```

   **E-commerce Schema Example:**
   ```sql
   -- Categories with hierarchical structure
   CREATE TABLE categories (
     id SERIAL PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     slug VARCHAR(255) UNIQUE NOT NULL,
     description TEXT,
     parent_id INTEGER REFERENCES categories(id),
     sort_order INTEGER DEFAULT 0,
     is_active BOOLEAN DEFAULT TRUE,
     meta_title VARCHAR(255),
     meta_description TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );

   -- Products table with comprehensive attributes
   CREATE TABLE products (
     id BIGSERIAL PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     slug VARCHAR(255) UNIQUE NOT NULL,
     sku VARCHAR(100) UNIQUE NOT NULL,
     description TEXT,
     short_description TEXT,
     price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
     compare_price DECIMAL(10,2) CHECK (compare_price >= price),
     cost_price DECIMAL(10,2) CHECK (cost_price >= 0),
     weight DECIMAL(8,2),
     dimensions JSONB, -- {length: x, width: y, height: z, unit: 'cm'}
     category_id INTEGER REFERENCES categories(id),
     brand_id INTEGER REFERENCES brands(id),
     vendor_id BIGINT REFERENCES vendors(id),
     status product_status DEFAULT 'draft',
     visibility product_visibility DEFAULT 'visible',
     inventory_tracking BOOLEAN DEFAULT TRUE,
     inventory_quantity INTEGER DEFAULT 0,
     low_stock_threshold INTEGER DEFAULT 5,
     allow_backorder BOOLEAN DEFAULT FALSE,
     requires_shipping BOOLEAN DEFAULT TRUE,
     is_digital BOOLEAN DEFAULT FALSE,
     tax_class VARCHAR(50) DEFAULT 'standard',
     featured BOOLEAN DEFAULT FALSE,
     tags TEXT[],
     attributes JSONB DEFAULT '{}',
     seo_title VARCHAR(255),
     seo_description TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     published_at TIMESTAMP WITH TIME ZONE,
     
     -- Full text search
     search_vector tsvector GENERATED ALWAYS AS (
       to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, '') || ' ' || COALESCE(sku, ''))
     ) STORED
   );

   -- Product status and visibility enums
   CREATE TYPE product_status AS ENUM ('draft', 'active', 'inactive', 'archived');
   CREATE TYPE product_visibility AS ENUM ('visible', 'hidden', 'catalog_only', 'search_only');

   -- Orders table with comprehensive tracking
   CREATE TABLE orders (
     id BIGSERIAL PRIMARY KEY,
     order_number VARCHAR(50) UNIQUE NOT NULL,
     user_id BIGINT REFERENCES users(id),
     status order_status DEFAULT 'pending',
     currency CHAR(3) DEFAULT 'USD',
     subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
     tax_total DECIMAL(10,2) NOT NULL DEFAULT 0,
     shipping_total DECIMAL(10,2) NOT NULL DEFAULT 0,
     discount_total DECIMAL(10,2) NOT NULL DEFAULT 0,
     total DECIMAL(10,2) NOT NULL DEFAULT 0,
     
     -- Billing information
     billing_first_name VARCHAR(100),
     billing_last_name VARCHAR(100),
     billing_company VARCHAR(255),
     billing_address_line_1 VARCHAR(255),
     billing_address_line_2 VARCHAR(255),
     billing_city VARCHAR(100),
     billing_state VARCHAR(100),
     billing_postal_code VARCHAR(20),
     billing_country CHAR(2),
     billing_phone VARCHAR(20),
     
     -- Shipping information
     shipping_first_name VARCHAR(100),
     shipping_last_name VARCHAR(100),
     shipping_company VARCHAR(255),
     shipping_address_line_1 VARCHAR(255),
     shipping_address_line_2 VARCHAR(255),
     shipping_city VARCHAR(100),
     shipping_state VARCHAR(100),
     shipping_postal_code VARCHAR(20),
     shipping_country CHAR(2),
     shipping_phone VARCHAR(20),
     shipping_method VARCHAR(100),
     tracking_number VARCHAR(255),
     
     notes TEXT,
     internal_notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     shipped_at TIMESTAMP WITH TIME ZONE,
     delivered_at TIMESTAMP WITH TIME ZONE
   );

   CREATE TYPE order_status AS ENUM (
     'pending', 'processing', 'shipped', 'delivered', 
     'cancelled', 'refunded', 'on_hold'
   );

   -- Order items with detailed tracking
   CREATE TABLE order_items (
     id BIGSERIAL PRIMARY KEY,
     order_id BIGINT REFERENCES orders(id) ON DELETE CASCADE,
     product_id BIGINT REFERENCES products(id),
     product_variant_id BIGINT REFERENCES product_variants(id),
     quantity INTEGER NOT NULL CHECK (quantity > 0),
     unit_price DECIMAL(10,2) NOT NULL,
     total_price DECIMAL(10,2) NOT NULL,
     product_name VARCHAR(255) NOT NULL, -- Snapshot at time of order
     product_sku VARCHAR(100), -- Snapshot at time of order
     product_attributes JSONB, -- Snapshot of selected variants
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Advanced Schema Patterns**
   - Implement complex data patterns:

   **Audit Trail Pattern:**
   ```sql
   -- Generic audit trail for tracking all changes
   CREATE TABLE audit_log (
     id BIGSERIAL PRIMARY KEY,
     table_name VARCHAR(255) NOT NULL,
     record_id BIGINT NOT NULL,
     operation audit_operation NOT NULL,
     old_values JSONB,
     new_values JSONB,
     changed_fields TEXT[],
     user_id BIGINT REFERENCES users(id),
     ip_address INET,
     user_agent TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     
     -- Index for efficient querying
     INDEX idx_audit_log_table_record (table_name, record_id),
     INDEX idx_audit_log_user_time (user_id, created_at),
     INDEX idx_audit_log_operation_time (operation, created_at)
   );

   CREATE TYPE audit_operation AS ENUM ('INSERT', 'UPDATE', 'DELETE');

   -- Trigger function for automatic audit logging
   CREATE OR REPLACE FUNCTION audit_trigger_function()
   RETURNS TRIGGER AS $$
   DECLARE
     old_data JSONB;
     new_data JSONB;
     changed_fields TEXT[];
   BEGIN
     IF TG_OP = 'DELETE' THEN
       old_data = to_jsonb(OLD);
       INSERT INTO audit_log (table_name, record_id, operation, old_values, user_id)
       VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', old_data, COALESCE(current_setting('app.current_user_id', true)::BIGINT, NULL));
       RETURN OLD;
     ELSIF TG_OP = 'UPDATE' THEN
       old_data = to_jsonb(OLD);
       new_data = to_jsonb(NEW);
       
       -- Find changed fields
       SELECT array_agg(key) INTO changed_fields
       FROM jsonb_each(old_data) 
       WHERE key IN (SELECT key FROM jsonb_each(new_data))
       AND value IS DISTINCT FROM (new_data->key);
       
       INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, changed_fields, user_id)
       VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', old_data, new_data, changed_fields, COALESCE(current_setting('app.current_user_id', true)::BIGINT, NULL));
       RETURN NEW;
     ELSIF TG_OP = 'INSERT' THEN
       new_data = to_jsonb(NEW);
       INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id)
       VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', new_data, COALESCE(current_setting('app.current_user_id', true)::BIGINT, NULL));
       RETURN NEW;
     END IF;
     RETURN NULL;
   END;
   $$ LANGUAGE plpgsql;
   ```

   **Soft Delete Pattern:**
   ```sql
   -- Add soft delete to any table
   ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
   ALTER TABLE products ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;

   -- Create views that exclude soft-deleted records
   CREATE VIEW active_users AS
   SELECT * FROM users WHERE deleted_at IS NULL;

   CREATE VIEW active_products AS
   SELECT * FROM products WHERE deleted_at IS NULL;

   -- Soft delete function
   CREATE OR REPLACE FUNCTION soft_delete(table_name TEXT, record_id BIGINT)
   RETURNS VOID AS $$
   BEGIN
     EXECUTE format('UPDATE %I SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL', table_name)
     USING record_id;
   END;
   $$ LANGUAGE plpgsql;

   -- Restore function
   CREATE OR REPLACE FUNCTION restore_deleted(table_name TEXT, record_id BIGINT)
   RETURNS VOID AS $$
   BEGIN
     EXECUTE format('UPDATE %I SET deleted_at = NULL WHERE id = $1', table_name)
     USING record_id;
   END;
   $$ LANGUAGE plpgsql;
   ```

4. **Performance Optimization Schema Design**
   - Design for optimal query performance:

   **Strategic Indexing:**
   ```sql
   -- Single column indexes for frequently queried fields
   CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
   CREATE INDEX CONCURRENTLY idx_users_username ON users(username);
   CREATE INDEX CONCURRENTLY idx_users_status ON users(status) WHERE status != 'active';
   CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);

   -- Composite indexes for common query patterns
   CREATE INDEX CONCURRENTLY idx_products_category_status 
   ON products(category_id, status) WHERE status = 'active';

   CREATE INDEX CONCURRENTLY idx_products_featured_category 
   ON products(featured, category_id) WHERE featured = true AND status = 'active';

   CREATE INDEX CONCURRENTLY idx_orders_user_status_date 
   ON orders(user_id, status, created_at);

   -- Partial indexes for specific conditions
   CREATE INDEX CONCURRENTLY idx_products_low_stock 
   ON products(inventory_quantity) 
   WHERE inventory_tracking = true AND inventory_quantity <= low_stock_threshold;

   -- Functional indexes for text search and computed values
   CREATE INDEX CONCURRENTLY idx_products_search_vector 
   ON products USING gin(search_vector);

   CREATE INDEX CONCURRENTLY idx_users_full_name_lower 
   ON users(lower(first_name || ' ' || last_name));

   -- JSON/JSONB indexes for flexible data
   CREATE INDEX CONCURRENTLY idx_user_profiles_notifications 
   ON user_profiles USING gin(notification_preferences);

   CREATE INDEX CONCURRENTLY idx_products_attributes 
   ON products USING gin(attributes);
   ```

   **Partitioning Strategy:**
   ```sql
   -- Partition large tables by date for better performance
   CREATE TABLE orders_partitioned (
     LIKE orders INCLUDING ALL
   ) PARTITION BY RANGE (created_at);

   -- Create monthly partitions
   CREATE TABLE orders_2024_01 PARTITION OF orders_partitioned
   FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

   CREATE TABLE orders_2024_02 PARTITION OF orders_partitioned
   FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

   -- Automatic partition management
   CREATE OR REPLACE FUNCTION create_monthly_partitions(
     table_name TEXT,
     start_date DATE,
     end_date DATE
   )
   RETURNS VOID AS $$
   DECLARE
     current_date DATE := start_date;
     partition_name TEXT;
     next_date DATE;
   BEGIN
     WHILE current_date < end_date LOOP
       next_date := current_date + INTERVAL '1 month';
       partition_name := table_name || '_' || to_char(current_date, 'YYYY_MM');
       
       EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
         partition_name, table_name, current_date, next_date);
       
       current_date := next_date;
     END LOOP;
   END;
   $$ LANGUAGE plpgsql;

   -- Schedule partition creation
   SELECT create_monthly_partitions('orders_partitioned', '2024-01-01'::DATE, '2025-01-01'::DATE);
   ```

5. **Data Integrity and Constraints**
   - Implement comprehensive data validation:

   **Advanced Constraints:**
   ```sql
   -- Complex check constraints
   ALTER TABLE products ADD CONSTRAINT products_price_logic 
   CHECK (
     CASE 
       WHEN compare_price IS NOT NULL THEN price <= compare_price
       ELSE true
     END
   );

   ALTER TABLE products ADD CONSTRAINT products_inventory_logic
   CHECK (
     CASE 
       WHEN inventory_tracking = false THEN inventory_quantity IS NULL
       WHEN inventory_tracking = true THEN inventory_quantity >= 0
       ELSE true
     END
   );

   -- Custom domain types for reusable validation
   CREATE DOMAIN email_address AS VARCHAR(255)
   CHECK (VALUE ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

   CREATE DOMAIN phone_number AS VARCHAR(20)
   CHECK (VALUE ~* '^\+?[\d\s\-\(\)]{10,20}$');

   CREATE DOMAIN positive_decimal AS DECIMAL(10,2)
   CHECK (VALUE >= 0);

   -- Use domains in table definitions
   CREATE TABLE contacts (
     id BIGSERIAL PRIMARY KEY,
     email email_address NOT NULL,
     phone phone_number,
     balance positive_decimal DEFAULT 0
   );

   -- Foreign key constraints with cascading options
   ALTER TABLE order_items 
   ADD CONSTRAINT fk_order_items_order 
   FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;

   ALTER TABLE order_items 
   ADD CONSTRAINT fk_order_items_product 
   FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;

   -- Unique constraints for business logic
   ALTER TABLE user_roles 
   ADD CONSTRAINT unique_user_role_active 
   UNIQUE (user_id, role_id);

   -- Exclusion constraints for complex business rules
   ALTER TABLE product_promotions 
   ADD CONSTRAINT no_overlapping_promotions 
   EXCLUDE USING gist (
     product_id WITH =,
     daterange(start_date, end_date, '[]') WITH &&
   );
   ```

6. **Temporal Data and Versioning**
   - Handle time-based data requirements:

   **Temporal Tables:**
   ```sql
   -- Product price history tracking
   CREATE TABLE product_price_history (
     id BIGSERIAL PRIMARY KEY,
     product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
     price DECIMAL(10,2) NOT NULL,
     compare_price DECIMAL(10,2),
     effective_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
     effective_to TIMESTAMP WITH TIME ZONE,
     created_by BIGINT REFERENCES users(id),
     reason TEXT,
     
     -- Ensure no overlapping periods
     EXCLUDE USING gist (
       product_id WITH =,
       tstzrange(effective_from, effective_to, '[)') WITH &&
     )
   );

   -- Function to get current price
   CREATE OR REPLACE FUNCTION get_current_price(p_product_id BIGINT)
   RETURNS DECIMAL(10,2) AS $$
   DECLARE
     current_price DECIMAL(10,2);
   BEGIN
     SELECT price INTO current_price
     FROM product_price_history
     WHERE product_id = p_product_id
     AND effective_from <= CURRENT_TIMESTAMP
     AND (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP)
     ORDER BY effective_from DESC
     LIMIT 1;
     
     RETURN current_price;
   END;
   $$ LANGUAGE plpgsql;

   -- Trigger to update price history when product price changes
   CREATE OR REPLACE FUNCTION update_price_history()
   RETURNS TRIGGER AS $$
   BEGIN
     IF OLD.price IS DISTINCT FROM NEW.price THEN
       -- Close current price period
       UPDATE product_price_history 
       SET effective_to = CURRENT_TIMESTAMP
       WHERE product_id = NEW.id AND effective_to IS NULL;
       
       -- Insert new price period
       INSERT INTO product_price_history (product_id, price, compare_price, created_by)
       VALUES (NEW.id, NEW.price, NEW.compare_price, 
               COALESCE(current_setting('app.current_user_id', true)::BIGINT, NULL));
     END IF;
     
     RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER trigger_product_price_history
   AFTER UPDATE ON products
   FOR EACH ROW
   EXECUTE FUNCTION update_price_history();
   ```

7. **JSON/NoSQL Integration**
   - Leverage JSON columns for flexible data:

   **JSONB Schema Design:**
   ```sql
   -- Flexible product attributes using JSONB
   CREATE TABLE product_attributes (
     product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
     attributes JSONB NOT NULL DEFAULT '{}',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     
     PRIMARY KEY (product_id)
   );

   -- JSONB indexes for efficient querying
   CREATE INDEX idx_product_attributes_gin ON product_attributes USING gin(attributes);
   CREATE INDEX idx_product_attributes_color ON product_attributes USING gin((attributes->'color'));
   CREATE INDEX idx_product_attributes_size ON product_attributes USING gin((attributes->'size'));

   -- Function to query products by attributes
   CREATE OR REPLACE FUNCTION find_products_by_attributes(search_attributes JSONB)
   RETURNS TABLE(product_id BIGINT, product_name VARCHAR, attributes JSONB) AS $$
   BEGIN
     RETURN QUERY
     SELECT p.id, p.name, pa.attributes
     FROM products p
     JOIN product_attributes pa ON p.id = pa.product_id
     WHERE pa.attributes @> search_attributes;
   END;
   $$ LANGUAGE plpgsql;

   -- Usage examples:
   -- SELECT * FROM find_products_by_attributes('{"color": "red", "size": "large"}');

   -- Settings table with JSONB for flexible configuration
   CREATE TABLE application_settings (
     id SERIAL PRIMARY KEY,
     category VARCHAR(100) NOT NULL,
     key VARCHAR(100) NOT NULL,
     value JSONB NOT NULL,
     description TEXT,
     is_public BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     
     UNIQUE(category, key)
   );

   -- Function to get setting value with type casting
   CREATE OR REPLACE FUNCTION get_setting(p_category VARCHAR, p_key VARCHAR, p_default ANYELEMENT DEFAULT NULL)
   RETURNS ANYELEMENT AS $$
   DECLARE
     setting_value JSONB;
   BEGIN
     SELECT value INTO setting_value
     FROM application_settings
     WHERE category = p_category AND key = p_key;
     
     IF setting_value IS NULL THEN
       RETURN p_default;
     END IF;
     
     RETURN (setting_value #>> '{}')::TEXT::pg_typeof(p_default);
   END;
   $$ LANGUAGE plpgsql;
   ```

8. **Database Security Schema**
   - Implement security at the schema level:

   **Row Level Security:**
   ```sql
   -- Enable RLS on sensitive tables
   ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
   ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

   -- Create policies for data access
   CREATE POLICY orders_user_access ON orders
   FOR ALL TO authenticated_users
   USING (user_id = current_user_id());

   CREATE POLICY orders_admin_access ON orders
   FOR ALL TO admin_users
   USING (true);

   -- Function to get current user ID from session
   CREATE OR REPLACE FUNCTION current_user_id()
   RETURNS BIGINT AS $$
   BEGIN
     RETURN COALESCE(current_setting('app.current_user_id', true)::BIGINT, 0);
   END;
   $$ LANGUAGE plpgsql SECURITY DEFINER;

   -- Create database roles with specific permissions
   CREATE ROLE app_readonly;
   GRANT CONNECT ON DATABASE myapp TO app_readonly;
   GRANT USAGE ON SCHEMA public TO app_readonly;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

   CREATE ROLE app_readwrite;
   GRANT app_readonly TO app_readwrite;
   GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_readwrite;

   -- Sensitive data encryption
   CREATE EXTENSION IF NOT EXISTS pgcrypto;

   -- Function to encrypt sensitive data
   CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT)
   RETURNS TEXT AS $$
   BEGIN
     RETURN encode(encrypt(data::bytea, current_setting('app.encryption_key'), 'aes'), 'base64');
   END;
   $$ LANGUAGE plpgsql;

   -- Function to decrypt sensitive data
   CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data TEXT)
   RETURNS TEXT AS $$
   BEGIN
     RETURN convert_from(decrypt(decode(encrypted_data, 'base64'), current_setting('app.encryption_key'), 'aes'), 'UTF8');
   END;
   $$ LANGUAGE plpgsql;
   ```

9. **Schema Documentation and Maintenance**
   - Document and maintain schema design:

   **Database Documentation:**
   ```sql
   -- Add comments to tables and columns
   COMMENT ON TABLE users IS 'User accounts and authentication information';
   COMMENT ON COLUMN users.email IS 'Unique email address for user authentication';
   COMMENT ON COLUMN users.status IS 'Current status of user account (active, inactive, suspended, pending_verification)';
   COMMENT ON COLUMN users.email_verified IS 'Whether the user has verified their email address';

   COMMENT ON TABLE products IS 'Product catalog with inventory and pricing information';
   COMMENT ON COLUMN products.search_vector IS 'Full-text search vector generated from name, description, and SKU';
   COMMENT ON COLUMN products.attributes IS 'Flexible product attributes stored as JSONB (color, size, material, etc.)';

   -- Create a view for schema documentation
   CREATE VIEW schema_documentation AS
   SELECT 
     t.table_name,
     t.table_type,
     obj_description(c.oid) AS table_comment,
     col.column_name,
     col.data_type,
     col.is_nullable,
     col.column_default,
     col_description(c.oid, col.ordinal_position) AS column_comment
   FROM information_schema.tables t
   JOIN pg_class c ON c.relname = t.table_name
   JOIN information_schema.columns col ON col.table_name = t.table_name
   WHERE t.table_schema = 'public'
   ORDER BY t.table_name, col.ordinal_position;
   ```

10. **Schema Testing and Validation**
    - Implement schema testing procedures:

    **Schema Validation Tests:**
    ```sql
    -- Test data integrity constraints
    DO $$
    DECLARE
      test_result BOOLEAN;
    BEGIN
      -- Test email validation
      BEGIN
        INSERT INTO users (email, username, password_hash, first_name, last_name)
        VALUES ('invalid-email', 'testuser', 'hash', 'Test', 'User');
        RAISE EXCEPTION 'Email validation failed - invalid email accepted';
      EXCEPTION
        WHEN check_violation THEN
          RAISE NOTICE 'Email validation working correctly';
      END;
      
      -- Test price constraints
      BEGIN
        INSERT INTO products (name, slug, sku, price, compare_price)
        VALUES ('Test Product', 'test-product', 'TEST-001', 100.00, 50.00);
        RAISE EXCEPTION 'Price validation failed - compare_price less than price accepted';
      EXCEPTION
        WHEN check_violation THEN
          RAISE NOTICE 'Price validation working correctly';
      END;
      
      -- Test foreign key constraints
      BEGIN
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price, product_name)
        VALUES (999999, 999999, 1, 10.00, 10.00, 'Test Product');
        RAISE EXCEPTION 'Foreign key validation failed - non-existent order_id accepted';
      EXCEPTION
        WHEN foreign_key_violation THEN
          RAISE NOTICE 'Foreign key validation working correctly';
      END;
    END;
    $$;

    -- Performance test queries
    CREATE OR REPLACE FUNCTION test_query_performance()
    RETURNS TABLE(test_name TEXT, execution_time INTERVAL) AS $$
    DECLARE
      start_time TIMESTAMP;
      end_time TIMESTAMP;
    BEGIN
      -- Test user lookup by email
      start_time := clock_timestamp();
      PERFORM * FROM users WHERE email = 'test@example.com';
      end_time := clock_timestamp();
      test_name := 'User lookup by email';
      execution_time := end_time - start_time;
      RETURN NEXT;
      
      -- Test product search
      start_time := clock_timestamp();
      PERFORM * FROM products WHERE search_vector @@ to_tsquery('english', 'laptop');
      end_time := clock_timestamp();
      test_name := 'Product full-text search';
      execution_time := end_time - start_time;
      RETURN NEXT;
      
      -- Test order history query
      start_time := clock_timestamp();
      PERFORM o.* FROM orders o 
      JOIN order_items oi ON o.id = oi.order_id 
      WHERE o.user_id = 1 
      ORDER BY o.created_at DESC 
      LIMIT 20;
      end_time := clock_timestamp();
      test_name := 'User order history';
      execution_time := end_time - start_time;
      RETURN NEXT;
    END;
    $$ LANGUAGE plpgsql;

    -- Run performance tests
    SELECT * FROM test_query_performance();
    ```