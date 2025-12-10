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
} from 'recharts';

interface DataPoint {
  period: string;
  pharmacies_with_orders: number;
  total_pharmacies?: number;
  pct_active?: number;
}

interface PharmacyComboChartProps {
  data: DataPoint[];
  title: string;
  totalPharmacies?: number; // If provided, shows as constant line
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
            const isPercentage = entry.dataKey === 'pct_active';
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

export default function PharmacyComboChart({ 
  data, 
  title,
  totalPharmacies
}: PharmacyComboChartProps) {
  // If totalPharmacies is provided, calculate percentage for each point
  const chartData = data.map(point => ({
    ...point,
    total_pharmacies: totalPharmacies || point.total_pharmacies || 0,
    pct_active: totalPharmacies && totalPharmacies > 0 
      ? (point.pharmacies_with_orders / totalPharmacies) * 100
      : point.pct_active || 0
  }));

  return (
    <div className="card">
      <div className="card-header bg-gray-50">
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart
            data={chartData}
            margin={{ top: 25, right: 60, left: 20, bottom: 5 }}
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
            {totalPharmacies && (
              <Bar
                yAxisId="left"
                dataKey="total_pharmacies"
                name="# Total Farmacias"
                fill="#166534"
                radius={[4, 4, 0, 0]}
                barSize={30}
              />
            )}
            
            {/* Pharmacies with orders bar (light green) */}
            <Bar
              yAxisId="left"
              dataKey="pharmacies_with_orders"
              name="# Farmacias con pedidos"
              fill="#4ade80"
              radius={[4, 4, 0, 0]}
              barSize={totalPharmacies ? 30 : 40}
            />
            
            {/* Percentage line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="pct_active"
              name="% Farmacias activas"
              stroke="#374151"
              strokeWidth={2}
              dot={{ fill: '#374151', strokeWidth: 2, r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

