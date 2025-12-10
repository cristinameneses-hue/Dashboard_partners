// Period Types
export type PeriodType = 
  | 'this_year' 
  | 'last_year' 
  | 'this_month' 
  | 'last_month' 
  | 'this_week' 
  | 'last_week' 
  | 'q1' 
  | 'q2' 
  | 'q3' 
  | 'q4' 
  | 'custom';

export interface PeriodFilter {
  period_type: PeriodType;
  start_date?: string;
  end_date?: string;
}

// Base Metrics (shared between Ecommerce and Shortage)
export interface BaseMetrics {
  gross_bookings: number;
  cancelled_bookings: number;
  net_bookings: number;
  gross_gmv: number;
  cancelled_gmv: number;
  net_gmv: number;
  average_ticket: number;
  avg_orders_per_pharmacy: number;
  avg_gmv_per_pharmacy: number;
  pct_cancelled_bookings: number;
  pct_cancelled_gmv: number;
}

// Ecommerce Metrics (per partner)
export interface EcommerceMetrics extends BaseMetrics {
  partner: string;
  pct_active_pharmacies: number | null;
  total_pharmacies_with_tag: number | null;
  pharmacies_with_orders: number;
}

// Ecommerce Response
export interface EcommerceResponse {
  period: PeriodFilter;
  period_start: string;
  period_end: string;
  partners: EcommerceMetrics[];
  totals: BaseMetrics;
}

// Time Series Types
export interface TimeSeriesPoint {
  period: string;
  gross_bookings: number;
  cancelled_bookings: number;
  net_bookings: number;
  gross_gmv: number;
  cancelled_gmv: number;
  net_gmv: number;
  pharmacies_with_orders: number;
  total_pharmacies: number;
  pct_pharmacies_active: number;
  average_ticket: number;
  avg_orders_per_pharmacy: number;
  avg_gmv_per_pharmacy: number;
}

export interface TimeSeriesResponse {
  group_by: string;
  data: TimeSeriesPoint[];
  total_pharmacies: number;
}

// Shortage Metrics (global)
export interface ShortageMetrics extends BaseMetrics {
  active_pharmacies: number;
  sending_pharmacies: number;
  receiving_pharmacies: number;
}

// Shortage Response
export interface ShortageResponse {
  period: PeriodFilter;
  period_start: string;
  period_end: string;
  metrics: ShortageMetrics;
}

// Partner Info
export interface PartnerInfo {
  id: string;
  name: string;
  has_tags: boolean;
}

// Pharmacy Distribution
export interface PharmacyDistribution {
  province?: string;
  city?: string;
  count: number;
}

export interface PartnerPharmacyDistribution {
  partner: string;
  pharmacies: number;
  tags: string[];
}

// Period options for UI
export const PERIOD_OPTIONS: { value: PeriodType; label: string; group: string }[] = [
  { value: 'this_month', label: 'Este Mes', group: 'Mes' },
  { value: 'last_month', label: 'Mes Anterior', group: 'Mes' },
  { value: 'this_week', label: 'Esta Semana', group: 'Semana' },
  { value: 'last_week', label: 'Semana Anterior', group: 'Semana' },
  { value: 'this_year', label: 'Este Año', group: 'Año' },
  { value: 'last_year', label: 'Año Anterior', group: 'Año' },
  { value: 'q1', label: 'Q1 (Ene-Mar)', group: 'Trimestre' },
  { value: 'q2', label: 'Q2 (Abr-Jun)', group: 'Trimestre' },
  { value: 'q3', label: 'Q3 (Jul-Sep)', group: 'Trimestre' },
  { value: 'q4', label: 'Q4 (Oct-Dic)', group: 'Trimestre' },
  { value: 'custom', label: 'Personalizado', group: 'Custom' },
];

// Partner Categories
export interface CategoryInfo {
  id: string;
  name: string;
  color: string;
  partners: string[];
}

export const PARTNER_CATEGORIES: CategoryInfo[] = [
  { 
    id: 'all', 
    name: 'Todos', 
    color: '#64748b',
    partners: []
  },
  { 
    id: 'um', 
    name: 'UM (Delivery)', 
    color: '#f59e0b',
    partners: ['glovo', 'uber', 'justeat'] 
  },
  { 
    id: 'marketplaces', 
    name: 'Marketplaces', 
    color: '#0ea5e9',
    partners: ['amazon'] 
  },
  { 
    id: 'retail', 
    name: 'Retail', 
    color: '#10b981',
    partners: ['carrefour'] 
  },
  { 
    id: 'otc', 
    name: 'OTC', 
    color: '#8b5cf6',
    partners: ['glovo-otc'] 
  },
  { 
    id: 'labs', 
    name: 'Labs', 
    color: '#ec4899',
    partners: ['danone', 'procter', 'enna', 'nordic', 'chiesi', 'ferrer'] 
  },
];

// Get category by partner
export function getCategoryByPartner(partner: string): CategoryInfo | undefined {
  return PARTNER_CATEGORIES.find(cat => 
    cat.partners.includes(partner.toLowerCase())
  );
}

// Get all partners list
export const ALL_PARTNERS = PARTNER_CATEGORIES
  .filter(cat => cat.id !== 'all')
  .flatMap(cat => cat.partners);
