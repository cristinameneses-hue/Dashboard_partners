export interface SchemaPermissions {
  [schema: string]: boolean;
}

export interface TableRow {
  table_name: string;
  name: string;
  database: string;
  description?: string;
  rowCount?: number;
  dataSize?: number;
  indexSize?: number;
  createTime?: string;
  updateTime?: string;
}

export interface ColumnRow {
  column_name: string;
  data_type: string;
}

// Re-export connection string types
export type {
  MySQLConnectionConfig,
  DatabasePermissions,
  DatabaseConfig,
  MultiDatabaseConfig,
  ConnectionStringEnvVars,
} from "./connection-strings.js";

// Re-export MongoDB types
export type {
  MongoDBConnectionConfig,
  MongoDBPermissions,
  MongoDBConfig,
  UnifiedDatabaseConfig,
} from "./mongodb-connections.js";
export { DatabaseType } from "./mongodb-connections.js";
