/**
 * Unified Database Manager
 *
 * Manages both MySQL and MongoDB connections in a unified interface
 */

import { DatabaseType, UnifiedDatabaseConfig } from "../types/mongodb-connections.js";
import { MultiDatabaseConfig, DatabaseConfig } from "../types/index.js";
import { MongoDBConfig } from "../types/mongodb-connections.js";
import { MultiConnectionManager, getConnectionManager } from "./multi-connection-manager.js";
import { MongoDBConnectionManager, getMongoDBConnectionManager } from "./mongodb-connection-manager.js";
import { log } from "../utils/index.js";

/**
 * Query result with metadata
 */
export interface QueryResult {
  /** Database type used */
  databaseType: DatabaseType;

  /** Database name */
  databaseName: string;

  /** Results data */
  data: any[];

  /** Row/document count */
  count: number;

  /** Query metadata */
  metadata?: {
    collection?: string;
    table?: string;
    executionTime?: number;
  };
}

/**
 * Unified database manager
 */
export class UnifiedDatabaseManager {
  private mysqlManager?: MultiConnectionManager;
  private mongoManager?: MongoDBConnectionManager;
  private databases: Map<string, UnifiedDatabaseConfig>;
  private defaultDatabase?: string;

  constructor(
    mysqlConfig?: MultiDatabaseConfig,
    mongoConfigs?: Map<string, MongoDBConfig>
  ) {
    this.databases = new Map();

    // Initialize MySQL databases
    if (mysqlConfig && mysqlConfig.databases.size > 0) {
      this.mysqlManager = getConnectionManager(mysqlConfig);

      mysqlConfig.databases.forEach((config, name) => {
        this.databases.set(name, {
          name,
          type: DatabaseType.MySQL,
          mysqlConfig: config,
          isDefault: config.isDefault,
        });

        if (config.isDefault) {
          this.defaultDatabase = name;
        }
      });
    }

    // Initialize MongoDB databases
    if (mongoConfigs && mongoConfigs.size > 0) {
      this.mongoManager = getMongoDBConnectionManager(mongoConfigs);

      mongoConfigs.forEach((config, name) => {
        this.databases.set(name, {
          name,
          type: DatabaseType.MongoDB,
          mongoConfig: config,
          isDefault: config.isDefault,
        });

        // If no MySQL default, use MongoDB default
        if (!this.defaultDatabase && config.isDefault) {
          this.defaultDatabase = name;
        }
      });
    }

    log("info", `Unified Database Manager initialized with ${this.databases.size} databases`);
  }

  /**
   * Get database configuration
   */
  public getDatabaseConfig(databaseName?: string): UnifiedDatabaseConfig {
    const dbName = databaseName?.toLowerCase() || this.defaultDatabase;

    if (!dbName) {
      throw new Error("No database specified and no default database configured");
    }

    const config = this.databases.get(dbName);
    if (!config) {
      throw new Error(`Database configuration not found: ${dbName}`);
    }

    return config;
  }

  /**
   * Execute SQL query on MySQL database
   */
  public async executeMySQL(
    sql: string,
    databaseName?: string
  ): Promise<QueryResult> {
    if (!this.mysqlManager) {
      throw new Error("No MySQL databases configured");
    }

    const config = this.getDatabaseConfig(databaseName);

    if (config.type !== DatabaseType.MySQL) {
      throw new Error(`Database ${config.name} is not a MySQL database`);
    }

    const startTime = Date.now();
    const results = await this.mysqlManager.executeQuery(sql, databaseName);
    const executionTime = Date.now() - startTime;

    return {
      databaseType: DatabaseType.MySQL,
      databaseName: config.name,
      data: results,
      count: results.length,
      metadata: {
        executionTime,
      },
    };
  }

  /**
   * Execute MongoDB query
   */
  public async executeMongoDB(
    collectionName: string,
    query: any = {},
    options?: any,
    databaseName?: string
  ): Promise<QueryResult> {
    if (!this.mongoManager) {
      throw new Error("No MongoDB databases configured");
    }

    const config = this.getDatabaseConfig(databaseName);

    if (config.type !== DatabaseType.MongoDB) {
      throw new Error(`Database ${config.name} is not a MongoDB database`);
    }

    const startTime = Date.now();
    const results = await this.mongoManager.executeQuery(
      collectionName,
      query,
      options,
      databaseName
    );
    const executionTime = Date.now() - startTime;

    return {
      databaseType: DatabaseType.MongoDB,
      databaseName: config.name,
      data: results,
      count: results.length,
      metadata: {
        collection: collectionName,
        executionTime,
      },
    };
  }

  /**
   * Execute MongoDB aggregation
   */
  public async executeMongoAggregation(
    collectionName: string,
    pipeline: any[],
    databaseName?: string
  ): Promise<QueryResult> {
    if (!this.mongoManager) {
      throw new Error("No MongoDB databases configured");
    }

    const config = this.getDatabaseConfig(databaseName);

    if (config.type !== DatabaseType.MongoDB) {
      throw new Error(`Database ${config.name} is not a MongoDB database`);
    }

    const startTime = Date.now();
    const results = await this.mongoManager.aggregate(
      collectionName,
      pipeline,
      databaseName
    );
    const executionTime = Date.now() - startTime;

    return {
      databaseType: DatabaseType.MongoDB,
      databaseName: config.name,
      data: results,
      count: results.length,
      metadata: {
        collection: collectionName,
        executionTime,
      },
    };
  }

  /**
   * List all databases
   */
  public listDatabases(): {
    name: string;
    type: DatabaseType;
    isDefault: boolean;
  }[] {
    return Array.from(this.databases.values()).map((config) => ({
      name: config.name,
      type: config.type,
      isDefault: config.isDefault || false,
    }));
  }

  /**
   * List MySQL databases
   */
  public listMySQLDatabases(): string[] {
    return Array.from(this.databases.values())
      .filter((config) => config.type === DatabaseType.MySQL)
      .map((config) => config.name);
  }

  /**
   * List MongoDB databases
   */
  public listMongoDBDatabases(): string[] {
    return Array.from(this.databases.values())
      .filter((config) => config.type === DatabaseType.MongoDB)
      .map((config) => config.name);
  }

  /**
   * Get database type
   */
  public getDatabaseType(databaseName: string): DatabaseType {
    const config = this.getDatabaseConfig(databaseName);
    return config.type;
  }

  /**
   * Check if database exists
   */
  public hasDatabase(databaseName: string): boolean {
    return this.databases.has(databaseName.toLowerCase());
  }

  /**
   * Get default database
   */
  public getDefaultDatabase(): string | undefined {
    return this.defaultDatabase;
  }

  /**
   * Test connection to database
   */
  public async testConnection(databaseName?: string): Promise<boolean> {
    const config = this.getDatabaseConfig(databaseName);

    try {
      if (config.type === DatabaseType.MySQL && this.mysqlManager) {
        return await this.mysqlManager.testConnection(databaseName);
      } else if (config.type === DatabaseType.MongoDB && this.mongoManager) {
        return await this.mongoManager.testConnection(databaseName);
      }
      return false;
    } catch (error) {
      log("error", `Connection test failed:`, error);
      return false;
    }
  }

  /**
   * Close all connections
   */
  public async closeAll(): Promise<void> {
    const promises: Promise<void>[] = [];

    if (this.mysqlManager) {
      promises.push(this.mysqlManager.closeAll());
    }

    if (this.mongoManager) {
      promises.push(this.mongoManager.closeAll());
    }

    await Promise.all(promises);

    log("info", "All database connections closed");
  }
}

// Export singleton instance
let instance: UnifiedDatabaseManager | null = null;

/**
 * Get singleton unified database manager
 */
export function getUnifiedDatabaseManager(
  mysqlConfig?: MultiDatabaseConfig,
  mongoConfigs?: Map<string, MongoDBConfig>
): UnifiedDatabaseManager {
  if (!instance) {
    instance = new UnifiedDatabaseManager(mysqlConfig, mongoConfigs);
  }
  return instance;
}

/**
 * Reset unified database manager
 */
export async function resetUnifiedDatabaseManager(): Promise<void> {
  if (instance) {
    await instance.closeAll();
    instance = null;
  }
}
