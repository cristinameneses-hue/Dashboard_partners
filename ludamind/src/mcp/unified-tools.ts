/**
 * Unified Database Tools for MCP Server
 *
 * Provides MCP tools for both MySQL and MongoDB with automatic routing
 */

import { UnifiedDatabaseManager } from "../db/unified-database-manager.js";
import { multiDbConfig, mongoDbConfigs } from "../config/index.js";
import { generateUnifiedDatabaseContext } from "../context/unified-database-context.js";
import { log } from "../utils/index.js";

// Singleton instance
let unifiedManager: UnifiedDatabaseManager | null = null;

/**
 * Initialize unified database manager
 */
export function getUnifiedManager(): UnifiedDatabaseManager {
  if (!unifiedManager) {
    log("info", "Initializing Unified Database Manager for MCP");
    unifiedManager = new UnifiedDatabaseManager(multiDbConfig, mongoDbConfigs);

    const databases = unifiedManager.listDatabases();
    log("info", `Unified Manager initialized with ${databases.length} databases:`);
    databases.forEach(db => {
      log("info", `  - ${db.name} (${db.type}) ${db.isDefault ? '[DEFAULT]' : ''}`);
    });
  }

  return unifiedManager;
}

/**
 * MCP Tool: unified_query
 * Executes queries on MySQL or MongoDB based on database type
 */
export const UnifiedQueryTool = {
  name: "unified_query",
  description: `Query both MySQL and MongoDB databases. The system will automatically route to the correct database.

  DATABASE ROUTING:
  - MySQL (trends): Use for analytics, ventas, trends, cazador, Z_Y scores, grupo de riesgo
  - MongoDB (ludafarma): Use for farmacias, usuarios, bookings, catálogo, pagos, notificaciones

  Specify the database type explicitly or let the context guide you.`,

  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "SQL query for MySQL or MongoDB query object (as JSON string) for MongoDB"
      },
      database: {
        type: "string",
        description: "Database name (e.g., 'trends' for MySQL, 'ludafarma' for MongoDB). Optional if you want auto-routing.",
        enum: [] as string[] // Will be populated dynamically
      },
      databaseType: {
        type: "string",
        description: "Type of database: 'mysql' or 'mongodb'. Optional if database name is provided.",
        enum: ["mysql", "mongodb"]
      },
      collection: {
        type: "string",
        description: "MongoDB collection name (required if databaseType is 'mongodb')"
      },
      mongoQuery: {
        type: "string",
        description: "MongoDB query object as JSON string (e.g., '{\"active\": 1}')"
      },
      mongoOptions: {
        type: "string",
        description: "MongoDB query options as JSON string (e.g., '{\"limit\": 10, \"sort\": {\"_id\": -1}}')"
      }
    },
    required: ["query"]
  },

  async handler(args: any) {
    const manager = getUnifiedManager();

    try {
      // Determine database type
      let dbType: "mysql" | "mongodb" | undefined;
      let dbName: string | undefined;

      if (args.database && typeof args.database === 'string') {
        const providedDbName: string = args.database;
        dbName = providedDbName;
        try {
          dbType = manager.getDatabaseType(providedDbName) as "mysql" | "mongodb";
        } catch (error: any) {
          return {
            content: [{
              type: "text",
              text: `Error: Database '${providedDbName}' not found. ${error.message}`
            }],
            isError: true
          };
        }
      } else if (args.databaseType) {
        dbType = args.databaseType as "mysql" | "mongodb";
      }

      if (!dbType) {
        return {
          content: [{
            type: "text",
            text: "Error: Could not determine database type. Please specify 'database' or 'databaseType'."
          }],
          isError: true
        };
      }

      // Execute based on type
      if (dbType === "mysql") {
        const sql = args.query;
        const result = await manager.executeMySQL(sql, dbName);

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              success: true,
              database: result.databaseName,
              databaseType: result.databaseType,
              count: result.count,
              data: result.data,
              metadata: result.metadata
            }, null, 2)
          }]
        };

      } else if (dbType === "mongodb") {
        if (!args.collection) {
          return {
            content: [{
              type: "text",
              text: "Error: 'collection' is required for MongoDB queries."
            }],
            isError: true
          };
        }

        // Parse MongoDB query and options
        const mongoQuery = args.mongoQuery ? JSON.parse(args.mongoQuery) : {};
        const mongoOptions = args.mongoOptions ? JSON.parse(args.mongoOptions) : {};

        const result = await manager.executeMongoDB(
          args.collection,
          mongoQuery,
          mongoOptions,
          dbName
        );

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              success: true,
              database: result.databaseName,
              databaseType: result.databaseType,
              collection: args.collection,
              count: result.count,
              data: result.data,
              metadata: result.metadata
            }, null, 2)
          }]
        };
      }

      return {
        content: [{
          type: "text",
          text: `Error: Unsupported database type: ${dbType}`
        }],
        isError: true
      };

    } catch (error: any) {
      log("error", "Error in unified_query tool:", error);
      return {
        content: [{
          type: "text",
          text: `Error executing query: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

/**
 * MCP Tool: list_databases
 * Lists all available databases (MySQL + MongoDB)
 */
export const ListDatabasesTool = {
  name: "list_databases",
  description: "Lists all available databases in the unified system (MySQL + MongoDB)",

  inputSchema: {
    type: "object",
    properties: {},
    required: []
  },

  async handler() {
    try {
      const manager = getUnifiedManager();
      const databases = manager.listDatabases();

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            total: databases.length,
            databases: databases,
            mysql: manager.listMySQLDatabases(),
            mongodb: manager.listMongoDBDatabases(),
            default: manager.getDefaultDatabase()
          }, null, 2)
        }]
      };
    } catch (error: any) {
      log("error", "Error in list_databases tool:", error);
      return {
        content: [{
          type: "text",
          text: `Error listing databases: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

/**
 * MCP Tool: get_routing_context
 * Returns the database routing rules for LLM
 */
export const GetRoutingContextTool = {
  name: "get_routing_context",
  description: "Get database routing rules to help decide between MySQL and MongoDB",

  inputSchema: {
    type: "object",
    properties: {},
    required: []
  },

  async handler() {
    try {
      const context = generateUnifiedDatabaseContext();

      return {
        content: [{
          type: "text",
          text: context
        }]
      };
    } catch (error: any) {
      log("error", "Error in get_routing_context tool:", error);
      return {
        content: [{
          type: "text",
          text: `Error getting routing context: ${error.message}`
        }],
        isError: true
      };
    }
  }
};

/**
 * Update tool schema with available databases
 */
export function updateToolSchemas() {
  const manager = getUnifiedManager();
  const databases = manager.listDatabases().map(db => db.name);

  // Update enum with actual database names
  (UnifiedQueryTool.inputSchema.properties.database as any).enum = databases;
}

/**
 * Export all unified tools
 */
export const UNIFIED_TOOLS = [
  UnifiedQueryTool,
  ListDatabasesTool,
  GetRoutingContextTool
];
