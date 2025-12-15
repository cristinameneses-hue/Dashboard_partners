/**
 * MongoDB Connection String Parser
 *
 * Parses MongoDB connection strings and environment variables
 */

import {
  MongoDBConnectionConfig,
  MongoDBPermissions,
  MongoDBConfig,
} from "../types/mongodb-connections.js";
import { log } from "./index.js";

/**
 * Parse MongoDB connection string
 *
 * Supported formats:
 * - mongodb://user:pass@host:port/database
 * - mongodb+srv://user:pass@cluster.mongodb.net/database
 * - mongodb://host1:port1,host2:port2/database?replicaSet=rs0
 *
 * @param connectionString - MongoDB connection URL
 * @returns Parsed connection configuration
 */
export function parseMongoDBConnectionString(
  connectionString: string
): MongoDBConnectionConfig {
  try {
    // Check protocol
    if (
      !connectionString.startsWith("mongodb://") &&
      !connectionString.startsWith("mongodb+srv://")
    ) {
      throw new Error(
        'MongoDB connection string must start with "mongodb://" or "mongodb+srv://"'
      );
    }

    const isSrv = connectionString.startsWith("mongodb+srv://");
    const protocol = isSrv ? "mongodb+srv://" : "mongodb://";

    // Remove protocol
    const withoutProtocol = connectionString.substring(protocol.length);

    // Find @ symbol (separates auth from hosts)
    const atIndex = withoutProtocol.indexOf("@");
    let user: string | undefined;
    let password: string | undefined;
    let hostsAndPath: string;

    if (atIndex > 0) {
      // Has authentication
      const authPart = withoutProtocol.substring(0, atIndex);
      hostsAndPath = withoutProtocol.substring(atIndex + 1);

      const colonIndex = authPart.indexOf(":");
      if (colonIndex > 0) {
        user = decodeURIComponent(authPart.substring(0, colonIndex));
        password = decodeURIComponent(authPart.substring(colonIndex + 1));
      } else {
        user = decodeURIComponent(authPart);
      }
    } else {
      // No authentication
      hostsAndPath = withoutProtocol;
    }

    // Separate hosts/database from query parameters
    const questionIndex = hostsAndPath.indexOf("?");
    const pathPart =
      questionIndex > 0
        ? hostsAndPath.substring(0, questionIndex)
        : hostsAndPath;
    const queryString =
      questionIndex > 0 ? hostsAndPath.substring(questionIndex + 1) : "";

    // Separate hosts from database
    const slashIndex = pathPart.indexOf("/");
    let hostsStr: string;
    let database: string;

    if (slashIndex > 0) {
      hostsStr = pathPart.substring(0, slashIndex);
      database = pathPart.substring(slashIndex + 1);
    } else {
      hostsStr = pathPart;
      database = "";
    }

    if (!database) {
      throw new Error("Database name is required in MongoDB connection string");
    }

    // Parse first host (for single host connections)
    const hosts = hostsStr.split(",");
    const firstHost = hosts[0];
    const hostParts = firstHost.split(":");

    const host = hostParts[0];
    const port = hostParts.length > 1 ? parseInt(hostParts[1], 10) : 27017;

    // Parse query parameters
    const options = parseMongoQueryString(queryString);

    return {
      host,
      port,
      user,
      password,
      database,
      replicaSet: options.replicaSet,
      ssl: options.ssl === "true" || options.tls === "true",
      authSource: options.authSource,
      options,
      connectionString, // Store original for driver
    };
  } catch (error) {
    throw new Error(
      `Failed to parse MongoDB connection string: ${
        error instanceof Error ? error.message : String(error)
      }`
    );
  }
}

/**
 * Parse MongoDB query string parameters
 */
function parseMongoQueryString(queryString: string): Record<string, string> {
  if (!queryString) return {};

  const params: Record<string, string> = {};

  queryString.split("&").forEach((param) => {
    const [key, value] = param.split("=");
    if (key) {
      params[key] = decodeURIComponent(value || "");
    }
  });

  return params;
}

/**
 * Parse MongoDB permissions from environment variables
 *
 * @param prefix - Environment variable prefix (e.g., "MONGO_MAIN")
 * @param env - Environment variables object
 * @returns MongoDB permissions
 */
export function parseMongoDBPermissions(
  prefix: string,
  env: Record<string, string | undefined>
): MongoDBPermissions {
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
 * Load MongoDB databases from environment variables
 *
 * Format:
 * MONGO_{NAME}_URL=mongodb://user:pass@host:port/database
 * MONGO_{NAME}_CAN_INSERT=true|false
 * MONGO_{NAME}_CAN_UPDATE=true|false
 * MONGO_{NAME}_CAN_DELETE=true|false
 * MONGO_{NAME}_CAN_DDL=true|false
 * MONGO_{NAME}_IS_DEFAULT=true|false
 *
 * @param env - Environment variables
 * @returns Map of MongoDB configurations
 */
export function loadMongoDBsFromEnv(
  env: Record<string, string | undefined>
): Map<string, MongoDBConfig> {
  const databases = new Map<string, MongoDBConfig>();

  // Find all MongoDB configurations
  const mongoPrefixes = new Set<string>();

  Object.keys(env).forEach((key) => {
    const match = key.match(/^MONGO_([A-Z0-9_]+)_URL$/);
    if (match) {
      mongoPrefixes.add(`MONGO_${match[1]}`);
    }
  });

  // Parse each MongoDB configuration
  mongoPrefixes.forEach((prefix) => {
    try {
      const connectionString = env[`${prefix}_URL`];

      if (!connectionString) {
        log("warn", `No connection string found for ${prefix}, skipping...`);
        return;
      }

      // Parse connection and permissions
      const connection = parseMongoDBConnectionString(connectionString);
      const permissions = parseMongoDBPermissions(prefix, env);

      // Extract database name from prefix
      const name = prefix.replace("MONGO_", "").toLowerCase();

      const isDefault = env[`${prefix}_IS_DEFAULT`] === "true";

      const config: MongoDBConfig = {
        name,
        connection,
        permissions,
        isDefault,
      };

      databases.set(name, config);

      log(
        "info",
        `Loaded MongoDB configuration: ${name} (${connection.host}:${connection.port}/${connection.database})`
      );
    } catch (error) {
      log(
        "error",
        `Failed to load MongoDB ${prefix}: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
    }
  });

  return databases;
}
