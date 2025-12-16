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
    'KPIs de Glovo: GMV total, cancelado, bookings',
    'Comparar totales absolutos de Madrid vs Barcelona este mes',
    'Comparar rendimiento medio por farmacia de Valencia vs Sevilla este mes',
    'GMV total de Uber esta semana',
    'Pedidos totales por partner',
    'GMV total del sistema (ecommerce vs shortage)',
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

// ============================================================================
// TIPOS PARA QUERIES PARAMETRIZABLES
// ============================================================================

// Opciones de periodo
export type PeriodOption = 'today' | 'this_week' | 'this_month' | 'last_quarter' | 'this_year' | 'custom';

// Opciones de partner
export type PartnerOption = 'all' | 'glovo' | 'uber' | 'justeat' | 'carrefour' | 'amazon' | 'danone' | 'procter' | 'enna' | 'nordic' | 'chiesi' | 'ferrer';

// Labels para periodos
export const PERIOD_LABELS: Record<PeriodOption, string> = {
  today: 'Hoy',
  this_week: 'Esta semana',
  this_month: 'Este mes',
  last_quarter: 'Ultimo trimestre',
  this_year: 'Este ano',
  custom: 'Personalizado',
};

// Labels para partners
export const PARTNER_LABELS: Record<PartnerOption, string> = {
  all: 'Todos',
  glovo: 'Glovo',
  uber: 'Uber',
  justeat: 'JustEat',
  carrefour: 'Carrefour',
  amazon: 'Amazon',
  danone: 'Danone',
  procter: 'Procter & Gamble',
  enna: 'Enna',
  nordic: 'Nordic',
  chiesi: 'Chiesi',
  ferrer: 'Ferrer',
};

// Lista de provincias disponibles (ordenadas por numero de farmacias)
export const PROVINCES: string[] = [
  'Madrid', 'Barcelona', 'Valencia', 'Alicante', 'Sevilla', 'Malaga', 'Murcia',
  'Toledo', 'Granada', 'Asturias', 'Illes Balears', 'Almeria', 'Navarra', 'Tarragona',
  'Cadiz', 'Valladolid', 'Santa Cruz de Tenerife', 'Girona', 'Zaragoza', 'Cordoba',
  'Las Palmas', 'Pontevedra', 'Huelva', 'Ciudad Real', 'A Coruna', 'Bizkaia', 'Leon',
  'Badajoz', 'Castello', 'Burgos', 'Gipuzkoa', 'Albacete', 'Cantabria', 'Jaen',
  'Caceres', 'Guadalajara', 'Araba', 'Lleida', 'Cuenca', 'Lugo', 'Zamora', 'Palencia',
  'La Rioja', 'Huesca', 'La Coruna', 'Salamanca', 'Segovia', 'Avila', 'Ourense',
  'Soria', 'Teruel', 'Castellon', 'Vizcaya', 'Melilla', 'Ceuta'
];

// Parametros de query
export interface QueryParams {
  period: PeriodOption;
  periodCustomStart?: string;
  periodCustomEnd?: string;
  partner: PartnerOption;
  province1?: string;
  province2?: string;
}

// Template de query parametrizable
export interface QueryTemplate {
  id: string;
  label: string;
  template: string;
  description: string;
  category: LudaMindMode;
  params: Array<'period' | 'partner' | 'province1' | 'province2'>;
}

// Templates de queries disponibles
export const QUERY_TEMPLATES: QueryTemplate[] = [
  // Partner queries
  {
    id: 'partner_kpis',
    label: 'KPIs de Partner',
    template: 'KPIs de {partner}: GMV total, cancelado, bookings en {period}',
    description: 'Metricas principales de un partner',
    category: 'partner',
    params: ['partner', 'period'],
  },
  {
    id: 'province_absolute',
    label: 'Comparativa Absoluta Provincias',
    template: 'Comparar totales absolutos de {province1} vs {province2} en {period}: farmacias activas, GMV total, pedidos totales, pedidos cancelados, porcentaje cancelacion, GMV cancelado, ticket medio',
    description: 'Compara volumenes totales entre provincias',
    category: 'partner',
    params: ['province1', 'province2', 'period'],
  },
  {
    id: 'province_average',
    label: 'Comparativa Media por Farmacia',
    template: 'Comparar rendimiento medio por farmacia de {province1} vs {province2} en {period}: GMV medio por farmacia, pedidos medio por farmacia, cancelados medio por farmacia, porcentaje cancelacion medio, ticket medio',
    description: 'Compara eficiencia media por farmacia entre provincias',
    category: 'partner',
    params: ['province1', 'province2', 'period'],
  },
];

// Funcion helper para construir query desde template
export function buildQueryFromTemplate(
  template: QueryTemplate,
  params: QueryParams
): string {
  let query = template.template;

  // Reemplazar periodo
  if (template.params.includes('period')) {
    const periodLabel = params.period === 'custom'
      ? `del ${params.periodCustomStart} al ${params.periodCustomEnd}`
      : PERIOD_LABELS[params.period].toLowerCase();
    query = query.replace('{period}', periodLabel);
  }

  // Reemplazar partner
  if (template.params.includes('partner')) {
    query = query.replace('{partner}', PARTNER_LABELS[params.partner]);
  }

  // Reemplazar provincias
  if (template.params.includes('province1') && params.province1) {
    query = query.replace('{province1}', params.province1);
  }
  if (template.params.includes('province2') && params.province2) {
    query = query.replace('{province2}', params.province2);
  }

  return query;
}
