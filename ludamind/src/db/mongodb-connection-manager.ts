/**
 * MongoDB Connection Manager
 *
 * Manages MongoDB client connections for different databases
 */

import { MongoClient, Db, Collection, Document } from "mongodb";
import { MongoDBConfig } from "../types/mongodb-connections.js";
import { log } from "../utils/index.js";

/**
 * MongoDB connection manager
 */
export class MongoDBConnectionManager {
  private clients: Map<string, MongoClient>;
  private databases: Map<string, Db>;
  private configs: Map<string, MongoDBConfig>;
  private defaultDatabase?: string;

  constructor(configs: Map<string, MongoDBConfig>) {
    this.clients = new Map();
    this.databases = new Map();
    this.configs = configs;

    // Find default database
    for (const [name, config] of configs.entries()) {
      if (config.isDefault) {
        this.defaultDatabase = name;
        break;
      }
    }
  }

  /**
   * Get or create MongoDB client and database
   */
  public async getDatabase(databaseName?: string): Promise<Db> {
    // Determine which database to use
    const dbName = databaseName?.toLowerCase() || this.defaultDatabase;

    if (!dbName) {
      throw new Error(
        "No database specified and no default MongoDB database configured"
      );
    }

    // Check if already connected
    if (this.databases.has(dbName)) {
      return this.databases.get(dbName)!;
    }

    // Get configuration
    const config = this.configs.get(dbName);
    if (!config) {
      throw new Error(`MongoDB configuration not found: ${dbName}`);
    }

    // Create client and connect
    const { client, db } = await this.createConnection(config);

    this.clients.set(dbName, client);
    this.databases.set(dbName, db);

    log("info", `Connected to MongoDB database: ${dbName}`);

    return db;
  }

  /**
   * Create MongoDB connection
   */
  private async createConnection(
    config: MongoDBConfig
  ): Promise<{ client: MongoClient; db: Db }> {
    const connectionString = config.connection.connectionString;

    const client = new MongoClient(connectionString, {
      maxPoolSize: 10,
      minPoolSize: 2,
      maxIdleTimeMS: 60000,
      serverSelectionTimeoutMS: 30000,
    });

    await client.connect();

    // Verify connection
    await client.db("admin").command({ ping: 1 });

    const db = client.db(config.connection.database);

    return { client, db };
  }

  /**
   * Get MongoDB database configuration
   */
  public getDatabaseConfig(databaseName?: string): MongoDBConfig {
    const dbName = databaseName?.toLowerCase() || this.defaultDatabase;

    if (!dbName) {
      throw new Error(
        "No database specified and no default MongoDB database configured"
      );
    }

    const config = this.configs.get(dbName);
    if (!config) {
      throw new Error(`MongoDB configuration not found: ${dbName}`);
    }

    return config;
  }

  /**
   * Get collection from database
   */
  public async getCollection<T extends Document = Document>(
    collectionName: string,
    databaseName?: string
  ): Promise<Collection<T>> {
    const db = await this.getDatabase(databaseName);
    return db.collection<T>(collectionName);
  }

  /**
   * List all collections in database
   */
  public async listCollections(databaseName?: string): Promise<string[]> {
    const db = await this.getDatabase(databaseName);
    const collections = await db.listCollections().toArray();
    return collections.map((col) => col.name);
  }

  /**
   * List all configured databases
   */
  public listDatabases(): string[] {
    return Array.from(this.configs.keys());
  }

  /**
   * Check if database exists in configuration
   */
  public hasDatabase(databaseName: string): boolean {
    return this.configs.has(databaseName.toLowerCase());
  }

  /**
   * Get default database name
   */
  public getDefaultDatabase(): string | undefined {
    return this.defaultDatabase;
  }

  /**
   * Test connection to database
   */
  public async testConnection(databaseName?: string): Promise<boolean> {
    try {
      const db = await this.getDatabase(databaseName);
      await db.command({ ping: 1 });
      return true;
    } catch (error) {
      log(
        "error",
        `MongoDB connection test failed for ${databaseName || "default"}:`,
        error
      );
      return false;
    }
  }

  /**
   * Execute query on MongoDB collection
   */
  public async executeQuery(
    collectionName: string,
    query: any,
    options?: any,
    databaseName?: string
  ): Promise<any[]> {
    const collection = await this.getCollection(
      collectionName,
      databaseName
    );
    return await collection.find(query, options).toArray();
  }

  /**
   * Count documents in collection
   */
  public async countDocuments(
    collectionName: string,
    query: any = {},
    databaseName?: string
  ): Promise<number> {
    const collection = await this.getCollection(collectionName, databaseName);
    return await collection.countDocuments(query);
  }

  /**
   * Aggregate on collection
   */
  public async aggregate<T extends Document = Document>(
    collectionName: string,
    pipeline: any[],
    databaseName?: string
  ): Promise<T[]> {
    const collection = await this.getCollection<T>(
      collectionName,
      databaseName
    );
    return await collection.aggregate<T>(pipeline).toArray();
  }

  /**
   * Insert document(s)
   */
  public async insertOne(
    collectionName: string,
    document: any,
    databaseName?: string
  ): Promise<any> {
    // Check permissions
    const config = this.getDatabaseConfig(databaseName);
    if (!config.permissions.canInsert) {
      throw new Error(
        `INSERT operation not allowed on database: ${databaseName || this.defaultDatabase}`
      );
    }

    const collection = await this.getCollection(collectionName, databaseName);
    return await collection.insertOne(document);
  }

  /**
   * Update document(s)
   */
  public async updateMany(
    collectionName: string,
    filter: any,
    update: any,
    databaseName?: string
  ): Promise<any> {
    // Check permissions
    const config = this.getDatabaseConfig(databaseName);
    if (!config.permissions.canUpdate) {
      throw new Error(
        `UPDATE operation not allowed on database: ${databaseName || this.defaultDatabase}`
      );
    }

    const collection = await this.getCollection(collectionName, databaseName);
    return await collection.updateMany(filter, update);
  }

  /**
   * Delete document(s)
   */
  public async deleteMany(
    collectionName: string,
    filter: any,
    databaseName?: string
  ): Promise<any> {
    // Check permissions
    const config = this.getDatabaseConfig(databaseName);
    if (!config.permissions.canDelete) {
      throw new Error(
        `DELETE operation not allowed on database: ${databaseName || this.defaultDatabase}`
      );
    }

    const collection = await this.getCollection(collectionName, databaseName);
    return await collection.deleteMany(filter);
  }

  /**
   * Close all connections
   */
  public async closeAll(): Promise<void> {
    const closePromises = Array.from(this.clients.values()).map((client) =>
      client.close()
    );

    await Promise.all(closePromises);

    this.clients.clear();
    this.databases.clear();

    log("info", "All MongoDB connections closed");
  }

  /**
   * Close specific database connection
   */
  public async closeConnection(databaseName: string): Promise<void> {
    const client = this.clients.get(databaseName.toLowerCase());

    if (client) {
      await client.close();
      this.clients.delete(databaseName.toLowerCase());
      this.databases.delete(databaseName.toLowerCase());
      log("info", `Closed MongoDB connection for database: ${databaseName}`);
    }
  }
}

// Export singleton instance
let instance: MongoDBConnectionManager | null = null;

/**
 * Get singleton MongoDB connection manager instance
 */
export function getMongoDBConnectionManager(
  configs?: Map<string, MongoDBConfig>
): MongoDBConnectionManager {
  if (!instance) {
    if (!configs) {
      throw new Error(
        "MongoDBConnectionManager not initialized. Provide configs on first call."
      );
    }
    instance = new MongoDBConnectionManager(configs);
  }
  return instance;
}

/**
 * Reset MongoDB connection manager (useful for testing)
 */
export async function resetMongoDBConnectionManager(): Promise<void> {
  if (instance) {
    await instance.closeAll();
    instance = null;
  }
}
