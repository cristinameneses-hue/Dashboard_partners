/**
 * Connection String Parser
 *
 * Parses MySQL connection strings and environment variables
 * to create multi-database configurations.
 */

import {
  MySQLConnectionConfig,
  DatabasePermissions,
  DatabaseConfig,
  MultiDatabaseConfig,
} from "../types/connection-strings.js";
import { log } from "./index.js";

/**
 * Parse MySQL connection string
 *
 * Supported formats:
 * - mysql://user:pass@host:port/database
 * - mysql://user:pass@host/database
 * - mysql://user@host:port/database
 * - mysql+socket:///path/to/socket/database
 *
 * @param connectionString - MySQL connection URL
 * @returns Parsed connection configuration
 */
export function parseConnectionString(
  connectionString: string
): MySQLConnectionConfig {
  try {
    // Handle socket connections
    if (connectionString.startsWith("mysql+socket://")) {
      // Format: mysql+socket:///path/to/socket/database?user=root&password=pass
      // We need to find the last / before ? to separate socket path from database
      const withoutProtocol = connectionString.replace("mysql+socket://", "");
      const queryIndex = withoutProtocol.indexOf("?");
      const pathPart =
        queryIndex > 0
          ? withoutProtocol.substring(0, queryIndex)
          : withoutProtocol;
      const queryString =
        queryIndex > 0 ? withoutProtocol.substring(queryIndex) : "";

      // Find last / in path
      const lastSlash = pathPart.lastIndexOf("/");
      if (lastSlash === -1) {
        throw new Error("Invalid socket connection string: missing database name");
      }

      const socketPath = pathPart.substring(0, lastSlash);
      const database = pathPart.substring(lastSlash + 1);

      if (!database) {
        throw new Error("Database name is required in socket connection string");
      }

      const options = parseQueryString(queryString);

      return {
        host: "localhost", // Not used with socket
        port: 3306, // Not used with socket
        user: options.user || "root",
        password: options.password || "",
        database: database,
        socketPath: socketPath,
        ssl: options.ssl === "true",
        options,
      };
    }

    // Handle TCP/IP connections
    const url = new URL(connectionString);

    if (url.protocol !== "mysql:") {
      throw new Error(
        `Unsupported protocol: ${url.protocol}. Use 'mysql://' or 'mysql+socket://'`
      );
    }

    const host = url.hostname || "127.0.0.1";
    const port = url.port ? parseInt(url.port, 10) : 3306;
    const user = url.username || "root";
    const password = decodeURIComponent(url.password || "");
    const database = url.pathname.slice(1); // Remove leading '/'

    if (!database) {
      throw new Error("Database name is required in connection string");
    }

    const options = parseQueryString(url.search);

    return {
      host,
      port,
      user,
      password,
      database,
      ssl: options.ssl === "true" || options.ssl === "1",
      options,
    };
  } catch (error) {
    throw new Error(
      `Failed to parse connection string: ${error instanceof Error ? error.message : String(error)}`
    );
  }
}

/**
 * Parse query string parameters
 */
function parseQueryString(queryString?: string): Record<string, string> {
  if (!queryString) return {};

  const params: Record<string, string> = {};
  const query = queryString.startsWith("?")
    ? queryString.slice(1)
    : queryString;

  query.split("&").forEach((param) => {
    const [key, value] = param.split("=");
    if (key) {
      params[key] = decodeURIComponent(value || "");
    }
  });

  return params;
}

/**
 * Parse permissions from environment variables
 *
 * @param prefix - Environment variable prefix (e.g., "TRENDS", "PRODUCTION")
 * @param env - Environment variables object
 * @returns Database permissions
 */
export function parsePermissions(
  prefix: string,
  env: Record<string, string | undefined>
): DatabasePermissions {
  const getBoolean = (key: string): boolean => {
    const value = env[`${prefix}_CAN_${key}`];
    return value === "true" || value === "1";
  };

  return {
    canInsert: getBoolean("INSERT"),
    canUpdate: getBoolean("UPDATE"),
    canDelete: getBoolean("DELETE"),
    canDdl: getBoolean("DDL"),
  };
}

/**
 * Load multi-database configuration from environment variables
 *
 * Supports two formats:
 *
 * Format 1 (New - Recommended):
 * DB_TRENDS_URL=mysql://root:pass@127.0.0.1:3307/trends
 * DB_TRENDS_CAN_INSERT=false
 * DB_TRENDS_CAN_UPDATE=false
 * DB_TRENDS_CAN_DELETE=false
 * DB_TRENDS_CAN_DDL=false
 *
 * Format 2 (Legacy):
 * TRENDS_CONNECTION_STRING=mysql://root:pass@127.0.0.1:3307/trends
 * TRENDS_CAN_INSERT=false
 *
 * @param env - Environment variables
 * @returns Multi-database configuration
 */
export function loadDatabasesFromEnv(
  env: Record<string, string | undefined>
): MultiDatabaseConfig {
  const databases = new Map<string, DatabaseConfig>();
  let defaultDatabase: string | undefined;

  // Find all database configurations
  const dbPrefixes = new Set<string>();

  // Look for Format 1: DB_{NAME}_URL
  Object.keys(env).forEach((key) => {
    const match = key.match(/^DB_([A-Z0-9_]+)_URL$/);
    if (match) {
      dbPrefixes.add(`DB_${match[1]}`);
    }
  });

  // Look for Format 2: {NAME}_CONNECTION_STRING
  Object.keys(env).forEach((key) => {
    const match = key.match(/^([A-Z0-9_]+)_CONNECTION_STRING$/);
    if (match && !match[1].startsWith("DB_")) {
      dbPrefixes.add(match[1]);
    }
  });

  // Parse each database configuration
  dbPrefixes.forEach((prefix) => {
    try {
      // Get connection string
      const connectionString =
        env[`${prefix}_URL`] || env[`${prefix}_CONNECTION_STRING`];

      if (!connectionString) {
        log(
          "warn",
          `No connection string found for ${prefix}, skipping...`
        );
        return;
      }

      // Parse connection and permissions
      const connection = parseConnectionString(connectionString);
      const permissions = parsePermissions(prefix, env);

      // Extract database name from prefix
      const name = prefix.startsWith("DB_")
        ? prefix.slice(3).toLowerCase()
        : prefix.toLowerCase();

      const isDefault = env[`${prefix}_IS_DEFAULT`] === "true";

      const config: DatabaseConfig = {
        name,
        connection,
        permissions,
        isDefault,
      };

      databases.set(name, config);

      if (isDefault) {
        defaultDatabase = name;
      }

      log(
        "info",
        `Loaded database configuration: ${name} (${connection.host}:${connection.port}/${connection.database})`
      );
    } catch (error) {
      log(
        "error",
        `Failed to load database ${prefix}: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  });

  // Fallback to legacy single database configuration
  if (databases.size === 0 && env.MYSQL_HOST && env.MYSQL_DB) {
    log("info", "No connection strings found, using legacy MYSQL_* variables");

    const legacyConfig: DatabaseConfig = {
      name: env.MYSQL_DB.toLowerCase(),
      connection: {
        host: env.MYSQL_HOST || "127.0.0.1",
        port: parseInt(env.MYSQL_PORT || "3306", 10),
        user: env.MYSQL_USER || "root",
        password: env.MYSQL_PASS || "",
        database: env.MYSQL_DB,
        socketPath: env.MYSQL_SOCKET_PATH,
        ssl: env.MYSQL_SSL === "true",
      },
      permissions: {
        canInsert: env.ALLOW_INSERT_OPERATION === "true",
        canUpdate: env.ALLOW_UPDATE_OPERATION === "true",
        canDelete: env.ALLOW_DELETE_OPERATION === "true",
        canDdl: env.ALLOW_DDL_OPERATION === "true",
      },
      isDefault: true,
    };

    databases.set(legacyConfig.name, legacyConfig);
    defaultDatabase = legacyConfig.name;

    log("info", `Loaded legacy database: ${legacyConfig.name}`);
  }

  return {
    databases,
    defaultDatabase,
  };
}

/**
 * Get database configuration by name
 *
 * @param config - Multi-database configuration
 * @param name - Database name (optional, uses default if not provided)
 * @returns Database configuration or undefined
 */
export function getDatabaseConfig(
  config: MultiDatabaseConfig,
  name?: string
): DatabaseConfig | undefined {
  if (name) {
    return config.databases.get(name.toLowerCase());
  }

  if (config.defaultDatabase) {
    return config.databases.get(config.defaultDatabase);
  }

  // Return first database if no default is set
  return config.databases.values().next().value;
}

/**
 * Check if operation is allowed for database
 *
 * @param config - Database configuration
 * @param operation - Operation type
 * @returns true if allowed
 */
export function isOperationAllowed(
  config: DatabaseConfig,
  operation: "insert" | "update" | "delete" | "ddl"
): boolean {
  switch (operation) {
    case "insert":
      return config.permissions.canInsert;
    case "update":
      return config.permissions.canUpdate;
    case "delete":
      return config.permissions.canDelete;
    case "ddl":
      return config.permissions.canDdl;
    default:
      return false;
  }
}
