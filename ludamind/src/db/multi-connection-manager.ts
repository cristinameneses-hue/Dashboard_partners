/**
 * Multi-Database Connection Manager
 *
 * Manages multiple MySQL connection pools for different databases
 */

import mysql from "mysql2/promise";
import type { Pool, PoolOptions, RowDataPacket } from "mysql2/promise";
import {
  DatabaseConfig,
  MultiDatabaseConfig,
  MySQLConnectionConfig,
} from "../types/index.js";
import { log } from "../utils/index.js";

/**
 * Connection pool manager
 */
export class MultiConnectionManager {
  private pools: Map<string, Pool>;
  private config: MultiDatabaseConfig;

  constructor(config: MultiDatabaseConfig) {
    this.pools = new Map();
    this.config = config;
  }

  /**
   * Get or create connection pool for database
   */
  public getPool(databaseName?: string): Pool {
    // Determine which database to use
    const dbName =
      databaseName?.toLowerCase() || this.config.defaultDatabase;

    if (!dbName) {
      throw new Error(
        "No database specified and no default database configured"
      );
    }

    // Check if pool already exists
    if (this.pools.has(dbName)) {
      return this.pools.get(dbName)!;
    }

    // Get database configuration
    const dbConfig = this.config.databases.get(dbName);
    if (!dbConfig) {
      throw new Error(`Database configuration not found: ${dbName}`);
    }

    // Create new pool
    const pool = this.createPool(dbConfig);
    this.pools.set(dbName, pool);

    log("info", `Created connection pool for database: ${dbName}`);

    return pool;
  }

  /**
   * Create MySQL connection pool from config
   */
  private createPool(dbConfig: DatabaseConfig): Pool {
    const conn = dbConfig.connection;

    const poolOptions: PoolOptions = {
      ...(conn.socketPath
        ? { socketPath: conn.socketPath }
        : {
            host: conn.host,
            port: conn.port,
          }),
      user: conn.user,
      password: conn.password,
      database: conn.database,
      connectionLimit: 10,
      waitForConnections: true,
      queueLimit: 0,
      enableKeepAlive: true,
      keepAliveInitialDelay: 0,
    };

    // Add SSL configuration if enabled
    if (conn.ssl) {
      poolOptions.ssl = {
        rejectUnauthorized:
          process.env.MYSQL_SSL_REJECT_UNAUTHORIZED === "true",
      };
    }

    return mysql.createPool(poolOptions);
  }

  /**
   * Get database configuration
   */
  public getDatabaseConfig(databaseName?: string): DatabaseConfig {
    const dbName =
      databaseName?.toLowerCase() || this.config.defaultDatabase;

    if (!dbName) {
      throw new Error(
        "No database specified and no default database configured"
      );
    }

    const dbConfig = this.config.databases.get(dbName);
    if (!dbConfig) {
      throw new Error(`Database configuration not found: ${dbName}`);
    }

    return dbConfig;
  }

  /**
   * List all configured databases
   */
  public listDatabases(): string[] {
    return Array.from(this.config.databases.keys());
  }

  /**
   * Check if database exists in configuration
   */
  public hasDatabase(databaseName: string): boolean {
    return this.config.databases.has(databaseName.toLowerCase());
  }

  /**
   * Get default database name
   */
  public getDefaultDatabase(): string | undefined {
    return this.config.defaultDatabase;
  }

  /**
   * Test connection to database
   */
  public async testConnection(databaseName?: string): Promise<boolean> {
    try {
      const pool = this.getPool(databaseName);
      const connection = await pool.getConnection();
      await connection.ping();
      connection.release();
      return true;
    } catch (error) {
      log(
        "error",
        `Connection test failed for ${databaseName || "default"}:`,
        error
      );
      return false;
    }
  }

  /**
   * Execute query on specific database
   */
  public async executeQuery<T extends RowDataPacket>(
    sql: string,
    databaseName?: string
  ): Promise<T[]> {
    const pool = this.getPool(databaseName);
    const [rows] = await pool.query<T[]>(sql);
    return rows;
  }

  /**
   * Close all connection pools
   */
  public async closeAll(): Promise<void> {
    const closePromises = Array.from(this.pools.values()).map((pool) =>
      pool.end()
    );

    await Promise.all(closePromises);

    this.pools.clear();
    log("info", "All database connection pools closed");
  }

  /**
   * Close specific database pool
   */
  public async closePool(databaseName: string): Promise<void> {
    const pool = this.pools.get(databaseName.toLowerCase());

    if (pool) {
      await pool.end();
      this.pools.delete(databaseName.toLowerCase());
      log("info", `Closed connection pool for database: ${databaseName}`);
    }
  }
}

// Export singleton instance
let instance: MultiConnectionManager | null = null;

/**
 * Get singleton connection manager instance
 */
export function getConnectionManager(
  config?: MultiDatabaseConfig
): MultiConnectionManager {
  if (!instance) {
    if (!config) {
      throw new Error(
        "MultiConnectionManager not initialized. Provide config on first call."
      );
    }
    instance = new MultiConnectionManager(config);
  }
  return instance;
}

/**
 * Reset connection manager (useful for testing)
 */
export async function resetConnectionManager(): Promise<void> {
  if (instance) {
    await instance.closeAll();
    instance = null;
  }
}
