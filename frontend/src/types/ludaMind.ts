/**
 * Tipos TypeScript para Luda Mind
 * Sistema de consultas inteligentes con IA
 */

// Modos de consulta disponibles
export type LudaMindMode = 'pharmacy' | 'product' | 'partner' | 'conversational';

// Configuración de cada modo
export interface ModeConfig {
  id: LudaMindMode;
  label: string;
  icon: string;
  description: string;
  color: string;
}

export const LUDA_MIND_MODES: ModeConfig[] = [
  {
    id: 'pharmacy',
    label: 'Farmacias',
    icon: '🏥',
    description: 'Análisis por farmacia',
    color: '#3b82f6' // blue
  },
  {
    id: 'product',
    label: 'Productos',
    icon: '💊',
    description: 'Ventas y stock',
    color: '#10b981' // green
  },
  {
    id: 'partner',
    label: 'Partners',
    icon: '🤝',
    description: 'Canales y GMV',
    color: '#f59e0b' // amber
  },
  {
    id: 'conversational',
    label: 'Conversacional',
    icon: '💬',
    description: 'Consultas abiertas',
    color: '#8b5cf6' // purple
  },
];

// Estructura de un mensaje en el chat
export interface LudaMindMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    database?: string;
    confidence?: number;
    mode?: string;
    method?: string;
  };
}

// Respuesta del backend Flask
export interface LudaMindResponse {
  success: boolean;
  answer: string;
  database: string;
  mode: string;
  confidence: number;
  timestamp: string;
  system: string;
  method?: string;
}

// Request para enviar query
export interface LudaMindQueryRequest {
  query: string;
  mode: LudaMindMode;
  session_id: string;
}

// Request para cambiar modo
export interface LudaMindModeRequest {
  session_id: string;
  mode: LudaMindMode;
}

// Entrada del historial
export interface HistoryEntry {
  query: string;
  mode: LudaMindMode;
  timestamp: string;
}

// Health check response
export interface LudaMindHealthResponse {
  status: string;
  system: string;
  version: string;
  databases: {
    mongodb: boolean;
    mysql: boolean;
  };
}

// Ejemplos de queries por modo
export const QUERY_EXAMPLES: Record<LudaMindMode, string[]> = {
  pharmacy: [
    'Mostrar farmacias activas en el sistema',
    'Farmacias activas en Madrid',
    'Total de farmacias registradas',
    'Farmacias por provincia',
    'Distribución geográfica de farmacias',
    'Farmacias con pedidos recientes',
  ],
  product: [
    'Catálogo de productos disponibles',
    'Total de productos en el sistema',
    'Buscar productos por categoría',
    'Productos activos vs inactivos',
    'Información de producto por EAN',
    'Precios de productos',
  ],
  partner: [
    'GMV total de Glovo esta semana',
    'GMV de Uber esta semana',
    'Comparación de GMV entre Glovo y Uber',
    'Pedidos totales por partner',
    'GMV total del sistema (ecommerce vs shortage)',
    'KPIs de Glovo: GMV total, cancelado, bookings',
  ],
  conversational: [
    'Dame un resumen ejecutivo del mes',
    '¿Cuáles son los principales KPIs actuales?',
    'Analiza las tendencias de ventas recientes',
    '¿Qué anomalías detectas en los datos?',
    'Compara el rendimiento actual vs mes anterior',
    'Dashboard general del negocio',
  ],
};

// Constantes
export const STORAGE_KEY = 'ludaMindHistory';
export const MAX_HISTORY_ITEMS = 20;
