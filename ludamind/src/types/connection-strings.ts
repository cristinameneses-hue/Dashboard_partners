/**
 * Connection String System - Types
 *
 * This module defines types for the new connection string-based
 * multi-database configuration system.
 */

/**
 * Parsed MySQL connection string components
 */
export interface MySQLConnectionConfig {
  /** MySQL host (e.g., "127.0.0.1", "localhost") */
  host: string;

  /** MySQL port (default: 3306) */
  port: number;

  /** MySQL username */
  user: string;

  /** MySQL password */
  password: string;

  /** Database name */
  database: string;

  /** Unix socket path (alternative to host:port) */
  socketPath?: string;

  /** SSL configuration */
  ssl?: boolean;

  /** Additional connection options */
  options?: Record<string, string>;
}

/**
 * Database-specific permissions
 */
export interface DatabasePermissions {
  /** Allow INSERT operations */
  canInsert: boolean;

  /** Allow UPDATE operations */
  canUpdate: boolean;

  /** Allow DELETE operations */
  canDelete: boolean;

  /** Allow DDL operations (CREATE TABLE, ALTER, etc.) */
  canDdl: boolean;
}

/**
 * Complete database configuration
 */
export interface DatabaseConfig {
  /** Database identifier/alias */
  name: string;

  /** Connection configuration */
  connection: MySQLConnectionConfig;

  /** Operation permissions */
  permissions: DatabasePermissions;

  /** Whether this is the default database */
  isDefault?: boolean;
}

/**
 * Multi-database configuration
 */
export interface MultiDatabaseConfig {
  /** Map of database name to configuration */
  databases: Map<string, DatabaseConfig>;

  /** Default database name (if any) */
  defaultDatabase?: string;
}

/**
 * Environment variable format for connection strings
 *
 * Format:
 * DB_{NAME}_URL=mysql://user:pass@host:port/database?options
 * DB_{NAME}_CAN_INSERT=true|false
 * DB_{NAME}_CAN_UPDATE=true|false
 * DB_{NAME}_CAN_DELETE=true|false
 * DB_{NAME}_CAN_DDL=true|false
 *
 * Or legacy format:
 * {NAME}_CONNECTION_STRING=mysql://user:pass@host:port/database
 * {NAME}_CAN_INSERT=true|false
 * {NAME}_CAN_UPDATE=true|false
 * {NAME}_CAN_DELETE=true|false
 * {NAME}_CAN_DDL=true|false
 */
export interface ConnectionStringEnvVars {
  [key: string]: string | undefined;
}
