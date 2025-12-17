import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { PARTNER_CATEGORIES, ALL_PARTNERS, getCategoryByPartner } from '../../types';

// Partner colors - matching the partners in PARTNER_CATEGORIES
const PARTNER_COLORS: Record<string, string> = {
  // UM (Delivery)
  'glovo': '#00C3A5',
  'uber': '#06C167',
  'justeat': '#FF8000',
  // Marketplaces
  'amazon': '#FF9900',
  // Retail
  'carrefour': '#004E98',
  // OTC
  'glovo-otc': '#8B5CF6',
  // Labs
  'danone': '#0073CF',
  'procter': '#1976D2',
  'enna': '#E91E63',
  'nordic': '#5C6BC0',
  'chiesi': '#00BCD4',
  'ferrer': '#009688',
};

// Get color for a partner
function getPartnerColor(partner: string, index: number): string {
  const key = partner.toLowerCase();
  if (PARTNER_COLORS[key]) {
    return PARTNER_COLORS[key];
  }
  // Fallback colors for unknown partners
  const fallbackColors = [
    '#3F51B5', '#009688', '#795548', '#607D8B', '#FF5722',
    '#CDDC39', '#4CAF50', '#2196F3', '#673AB7', '#FFC107'
  ];
  return fallbackColors[index % fallbackColors.length];
}

export type ViewMode = 'partners' | 'categories';

interface PartnerStackedChartProps {
  data: any[];
  title: string;
  type: 'orders' | 'gmv';
  isPercentage?: boolean;
  viewMode?: ViewMode;
  selectedPartners?: string[]; // Partners selected in the main filter
}

// Format numbers with thousands separator
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(0)}K`;
  }
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 0
  }).format(Math.round(num));
}

// Format currency
function formatCurrency(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M €`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(0)}K €`;
  }
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(Math.round(num));
}

// Normalize partner name for comparison
function normalizePartnerName(name: string): string {
  return name.toLowerCase().replace(/[-_\s]/g, '');
}

// Check if a partner from data matches any in the allowed list
function isPartnerAllowed(dataPartner: string, allowedPartners: string[]): boolean {
  const normalizedData = normalizePartnerName(dataPartner);
  return allowedPartners.some(allowed => {
    const normalizedAllowed = normalizePartnerName(allowed);
    return normalizedData === normalizedAllowed || 
           normalizedData.includes(normalizedAllowed) ||
           normalizedAllowed.includes(normalizedData);
  });
}

// Filter data to only include specified partners
function filterPartners(data: any[], allowedPartners: string[]): any[] {
  if (!data || data.length === 0) return [];
  
  return data.map(point => {
    const filtered: any = { period: point.period };
    Object.keys(point).forEach(key => {
      if (key === 'period') return;
      if (isPartnerAllowed(key, allowedPartners)) {
        filtered[key] = point[key];
      }
    });
    return filtered;
  });
}

// Group data by categories (only for categories that have data)
function groupByCategories(data: any[], allowedPartners: string[]): any[] {
  if (!data || data.length === 0) return [];
  
  // Get categories that have at least one allowed partner
  const relevantCategories = PARTNER_CATEGORIES.filter(cat => {
    if (cat.id === 'all') return false;
    return cat.partners.some(p => 
      allowedPartners.some(allowed => normalizePartnerName(p) === normalizePartnerName(allowed))
    );
  });
  
  return data.map(point => {
    const grouped: any = { period: point.period };
    
    // Initialize only relevant category totals
    relevantCategories.forEach(cat => {
      grouped[cat.name] = 0;
    });
    
    // Sum up values by category
    Object.keys(point).forEach(key => {
      if (key === 'period') return;
      const category = getCategoryByPartner(key);
      if (category && grouped.hasOwnProperty(category.name)) {
        grouped[category.name] = (grouped[category.name] || 0) + (point[key] || 0);
      }
    });
    
    return grouped;
  });
}

// Custom tooltip
function CustomTooltip({ active, payload, label, type, isPercentage }: any) {
  if (!active || !payload?.length) return null;

  // Sort payload by value descending
  const sortedPayload = [...payload].sort((a, b) => (b.value || 0) - (a.value || 0));

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm max-h-80 overflow-y-auto">
      <p className="font-semibold text-gray-800 mb-2">{label}</p>
      {sortedPayload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2 mb-1">
          <div 
            className="w-3 h-3 rounded-sm flex-shrink-0"
            style={{ backgroundColor: entry.fill }}
          />
          <span className="text-gray-600 capitalize truncate max-w-[120px]">{entry.name.replace('-', ' ')}:</span>
          <span className="font-medium text-gray-800">
            {isPercentage 
              ? `${entry.value.toFixed(1)}%`
              : type === 'gmv' 
                ? formatCurrency(entry.value) 
                : formatNumber(entry.value)
            }
          </span>
        </div>
      ))}
    </div>
  );
}

export default function PartnerStackedChart({ 
  data, 
  title, 
  type, 
  isPercentage = false,
  viewMode = 'partners',
  selectedPartners = []
}: PartnerStackedChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
        <div className="card-body h-64 flex items-center justify-center text-gray-500">
          No hay datos disponibles
        </div>
      </div>
    );
  }

  // Determine which partners to show
  // If selectedPartners is empty, show all partners from ALL_PARTNERS
  // If selectedPartners has values, show only those
  const partnersToShow = selectedPartners.length > 0 
    ? selectedPartners 
    : ALL_PARTNERS;

  // Filter data to only show allowed partners
  const filteredData = filterPartners(data, partnersToShow);
  
  // Group by categories if needed
  const processedData = viewMode === 'categories' 
    ? groupByCategories(filteredData, partnersToShow)
    : filteredData;

  // Get unique keys (partners or categories) from data
  const keys = processedData.length > 0 
    ? Object.keys(processedData[0]).filter(k => k !== 'period' && processedData.some(d => (d[k] || 0) > 0))
    : [];

  // Transform data for percentage view
  const chartData = isPercentage
    ? processedData.map(point => {
        const total = keys.reduce((sum, k) => sum + (point[k] || 0), 0);
        const transformed: any = { period: point.period };
        keys.forEach(k => {
          transformed[k] = total > 0 ? ((point[k] || 0) / total) * 100 : 0;
        });
        return transformed;
      })
    : processedData;

  // Get color function based on view mode
  const getColor = viewMode === 'categories' 
    ? (key: string, _index: number) => {
        const category = PARTNER_CATEGORIES.find(cat => cat.name === key);
        return category?.color || '#94A3B8';
      }
    : getPartnerColor;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <XAxis 
              dataKey="period" 
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickFormatter={(value) => 
                isPercentage 
                  ? `${Math.round(value)}%` 
                  : type === 'gmv' 
                    ? formatCurrency(value)
                    : formatNumber(value)
              }
              domain={isPercentage ? [0, 100] : ['auto', 'auto']}
              ticks={isPercentage ? [0, 20, 40, 60, 80, 100] : undefined}
            />
            <Tooltip content={<CustomTooltip type={type} isPercentage={isPercentage} />} />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              formatter={(value: string) => (
                <span className="text-xs text-gray-600 capitalize">{value.replace('-', ' ')}</span>
              )}
            />
            {keys.map((key, index) => (
              <Bar
                key={key}
                dataKey={key}
                stackId="stack"
                fill={getColor(key, index)}
                name={key}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
