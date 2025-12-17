import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

// Extended partner colors palette - one unique color for each partner
const PARTNER_COLORS: Record<string, string> = {
  // Delivery partners
  'glovo': '#00C3A5',
  'glovo otc': '#00A896',
  'uber': '#06C167',
  'uber-eats': '#06C167',
  'justeat': '#FF8000',
  'just-eat': '#FF8000',
  // Retail & marketplaces
  'carrefour': '#004E98',
  'amazon': '#FF9900',
  'enna': '#E91E63',
  'danone': '#0073CF',
  'nordic': '#5C6BC0',
  'perfumesclub': '#9C27B0',
  // Miravia partners
  'trebol miravia-lc': '#F44336',
  'nervion miravia-lc': '#E53935',
  'pierre fabre-miravia': '#D32F2F',
  'b58 miravia-lc': '#C62828',
  // Pharmacies & labs
  'ludaalmacen': '#00A651',
  'luda-farma': '#00A651',
  'ludafarma': '#00A651',
  'retail': '#6366F1',
  'labs': '#8B5CF6',
  // Others
  'procter': '#1976D2',
  'hartmann': '#00BCD4',
};

// Fallback color palette for unknown partners
const FALLBACK_COLORS = [
  '#3F51B5', '#009688', '#795548', '#607D8B', '#FF5722',
  '#CDDC39', '#4CAF50', '#2196F3', '#673AB7', '#FFC107',
  '#03A9F4', '#8BC34A', '#FF4081', '#00BFA5', '#7C4DFF'
];

// Get color for a partner
function getPartnerColor(partner: string, index: number): string {
  const key = partner.toLowerCase();
  if (PARTNER_COLORS[key]) {
    return PARTNER_COLORS[key];
  }
  // Use fallback color based on index
  return FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

interface PartnerStackedChartProps {
  data: any[];
  title: string;
  type: 'orders' | 'gmv';
  isPercentage?: boolean;
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

// Custom tooltip
function CustomTooltip({ active, payload, label, type, isPercentage }: any) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800 mb-2">{label}</p>
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2 mb-1">
          <div 
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: entry.fill }}
          />
          <span className="text-gray-600 capitalize">{entry.name.replace('-', ' ')}:</span>
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

export default function PartnerStackedChart({ data, title, type, isPercentage = false }: PartnerStackedChartProps) {
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

  // Get unique partners from data
  const partners = data.length > 0 ? Object.keys(data[0]).filter(k => k !== 'period') : [];

  // Transform data for percentage view
  const chartData = isPercentage
    ? data.map(point => {
        const total = partners.reduce((sum, p) => sum + (point[p] || 0), 0);
        const transformed: any = { period: point.period };
        partners.forEach(p => {
          transformed[p] = total > 0 ? ((point[p] || 0) / total) * 100 : 0;
        });
        return transformed;
      })
    : data;

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
            {partners.map((partner, index) => (
              <Bar
                key={partner}
                dataKey={partner}
                stackId="stack"
                fill={getPartnerColor(partner, index)}
                name={partner}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

