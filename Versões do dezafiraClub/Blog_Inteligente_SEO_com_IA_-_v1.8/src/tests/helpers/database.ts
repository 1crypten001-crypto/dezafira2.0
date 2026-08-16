/**
 * Database Test Helpers
 * 
 * Utilities for setting up and tearing down test databases.
 */

import { Pool } from 'pg';

/**
 * Create a test database pool with custom configuration
 */
export function createTestPool(config?: {
    min?: number;
    max?: number;
    connectionTimeoutMillis?: number;
    idleTimeoutMillis?: number;
}): Pool {
    return new Pool({
        host: process.env.DB_HOST || 'localhost',
        port: parseInt(process.env.DB_PORT || '5432'),
        database: process.env.DB_NAME || 'blog_cms_test',
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'postgres',
        min: config?.min ?? 2,
        max: config?.max ?? 10,
        connectionTimeoutMillis: config?.connectionTimeoutMillis ?? 5000,
        idleTimeoutMillis: config?.idleTimeoutMillis ?? 30000,
    });
}

/**
 * Wait for a specified amount of time
 */
export function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Create a test tenant for multi-tenancy tests
 */
export async function createTestTenant(pool: Pool): Promise<string> {
    const result = await pool.query(
        `INSERT INTO tenants (slug, name, status) 
         VALUES ($1, $2, $3) 
         RETURNING id`,
        ['test-tenant', 'Test Tenant', 'active']
    );
    return result.rows[0].id;
}

/**
 * Clean up test tenant
 */
export async function cleanupTestTenant(pool: Pool, tenantId: string): Promise<void> {
    await pool.query('DELETE FROM tenants WHERE id = $1', [tenantId]);
}

/**
 * Setup test database schema (if needed)
 */
export async function setupTestDatabase(pool: Pool): Promise<void> {
    // Enable UUID extension
    await pool.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');
    
    // Create tenants table if it doesn't exist
    await pool.query(`
        CREATE TABLE IF NOT EXISTS tenants (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            slug VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            custom_domain VARCHAR(255) UNIQUE,
            status VARCHAR(20) DEFAULT 'active',
            settings JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    `);
}

/**
 * Teardown test database (clean up test data)
 */
export async function teardownTestDatabase(pool: Pool): Promise<void> {
    // Clean up test data
    await pool.query('DELETE FROM tenants WHERE slug LIKE $1', ['test-%']);
}
