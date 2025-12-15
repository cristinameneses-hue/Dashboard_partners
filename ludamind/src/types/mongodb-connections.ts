/**
 * MongoDB Connection String Types
 *
 * Types for MongoDB connection string-based configuration
 */

/**
 * Parsed MongoDB connection string components
 */
export interface MongoDBConnectionConfig {
  /** MongoDB host (e.g., "localhost", "cluster.mongodb.net") */
  host: string;

  /** MongoDB port (default: 27017) */
  port: number;

  /** MongoDB username */
  user?: string;

  /** MongoDB password */
  password?: string;

  /** Database name */
  database: string;

  /** Replica set name */
  replicaSet?: string;

  /** Use SSL/TLS */
  ssl?: boolean;

  /** Authentication database */
  authSource?: string;

  /** Additional connection options */
  options?: Record<string, string>;

  /** Full connection string (for mongodb driver) */
  connectionString: string;
}

/**
 * Database-specific permissions for MongoDB
 */
export interface MongoDBPermissions {
  /** Allow insert operations */
  canInsert: boolean;

  /** Allow update operations */
  canUpdate: boolean;

  /** Allow delete operations */
  canDelete: boolean;

  /** Allow createCollection/dropCollection */
  canDdl: boolean;
}

/**
 * Complete MongoDB database configuration
 */
export interface MongoDBConfig {
  /** Database identifier/alias */
  name: string;

  /** Connection configuration */
  connection: MongoDBConnectionConfig;

  /** Operation permissions */
  permissions: MongoDBPermissions;

  /** Whether this is the default database */
  isDefault?: boolean;
}

/**
 * Database type enumeration
 */
export enum DatabaseType {
  MySQL = "mysql",
  MongoDB = "mongodb",
}

/**
 * Unified database configuration (MySQL or MongoDB)
 */
export interface UnifiedDatabaseConfig {
  /** Database name/alias */
  name: string;

  /** Database type */
  type: DatabaseType;

  /** MySQL config (if type is MySQL) */
  mysqlConfig?: any; // Will use DatabaseConfig from connection-strings.ts

  /** MongoDB config (if type is MongoDB) */
  mongoConfig?: MongoDBConfig;

  /** Is this the default database */
  isDefault?: boolean;
}
