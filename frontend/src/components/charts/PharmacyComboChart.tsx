import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

interface DataPoint {
  period: string;
  pharmacies_with_orders: number;
  total_pharmacies: number;
  pct_pharmacies_active: number;
}

interface PharmacyComboChartProps {
  data: DataPoint[];
  title: string;
  height?: number;
  showHeader?: boolean;
}

// Format numbers with thousands separator
function formatNumber(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 0
  }).format(Math.round(num));
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-800 mb-2">{label}</p>
        <div className="space-y-1 text-sm">
          {payload.map((entry: any, index: number) => {
            const isPercentage = entry.dataKey === 'pct_pharmacies_active';
            const value = isPercentage 
              ? `${entry.value?.toFixed(1)}%` 
              : formatNumber(entry.value || 0);
            
            return (
              <div key={index} className="flex justify-between gap-4">
                <span style={{ color: entry.color }}>{entry.name}:</span>
                <span className="font-medium" style={{ color: entry.color }}>{value}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
};

// Custom label renderer for percentage line
const renderPercentLabel = (props: any) => {
  const { x, y, value } = props;
  if (value === undefined || value === null) return null;
  return (
    <text
      x={x}
      y={y - 10}
      fill="#374151"
      textAnchor="middle"
      fontSize={10}
      fontWeight={600}
    >
      {value.toFixed(1)}%
    </text>
  );
};

export default function PharmacyComboChart({ 
  data, 
  title,
  height = 320,
  showHeader = true
}: PharmacyComboChartProps) {
  return (
    <div className="card h-full flex flex-col">
      {showHeader && (
        <div className="card-header bg-gray-50">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className="card-body flex-1">
        <ResponsiveContainer width="100%" height={height}>
          <ComposedChart
            data={data}
            margin={{ top: 30, right: 60, left: 20, bottom: 5 }}
            barGap={2}
            barCategoryGap="20%"
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="period" 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={{ stroke: '#d1d5db' }}
            />
            <YAxis 
              yAxisId="left"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={{ stroke: '#d1d5db' }}
              tickFormatter={(value) => formatNumber(value)}
            />
            <YAxis 
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={{ stroke: '#d1d5db' }}
              tickFormatter={(value) => `${value}%`}
              domain={[0, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ paddingTop: 10 }} />
            
            {/* Total pharmacies bar (dark green) */}
            <Bar
              yAxisId="left"
              dataKey="total_pharmacies"
              name="# Total Farmacias"
              fill="#166534"
              radius={[4, 4, 0, 0]}
              maxBarSize={35}
            >
              <LabelList 
                dataKey="total_pharmacies" 
                position="top" 
                fill="#166534"
                fontSize={10}
                formatter={(value: number) => formatNumber(value)}
              />
            </Bar>
            
            {/* Pharmacies with orders bar (light green) */}
            <Bar
              yAxisId="left"
              dataKey="pharmacies_with_orders"
              name="# Fcias. ≥1 pedido"
              fill="#4ade80"
              radius={[4, 4, 0, 0]}
              maxBarSize={35}
            >
              <LabelList 
                dataKey="pharmacies_with_orders" 
                position="top" 
                fill="#22c55e"
                fontSize={10}
                formatter={(value: number) => formatNumber(value)}
              />
            </Bar>
            
            {/* Percentage line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="pct_pharmacies_active"
              name="% Fcias. ≥1 pedido"
              stroke="#374151"
              strokeWidth={2}
              dot={{ fill: '#374151', strokeWidth: 2, r: 4 }}
              label={renderPercentLabel}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
