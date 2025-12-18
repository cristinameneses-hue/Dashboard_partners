import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LabelList,
} from 'recharts';
import type { ShortageTimeSeriesPoint } from '../../types';

interface ShortageOpsGMVComboProps {
  data: ShortageTimeSeriesPoint[];
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

// Format currency without decimals
function formatCurrency(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(Math.round(num));
}

// Format for Y-axis labels (abbreviated)
function formatAxisNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
  return num.toString();
}

function formatAxisCurrency(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M €`;
  if (num >= 1000) return `${(num / 1000).toFixed(0)}K €`;
  return `${num} €`;
}

// Custom label for GMV value on top of bars
function GMVLabel({ x, y, width, value }: any) {
  if (!value || value === 0) return null;
  
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      textAnchor="middle"
      fill="#00A651"
      fontSize={10}
      fontWeight={600}
    >
      {formatCurrency(value)}
    </text>
  );
}

// Custom tooltip
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;

  const data = payload[0]?.payload;
  if (!data) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800 mb-2">{label}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Gross GMV:</span>
          <span className="font-medium text-[#00A651]">
            {formatCurrency(data.gross_gmv)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Gross Ops:</span>
          <span className="font-medium text-gray-800">
            {formatNumber(data.gross_bookings)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ShortageOpsGMVCombo({ 
  data, 
  title,
  height = 320,
  showHeader = true 
}: ShortageOpsGMVComboProps) {
  if (!data || data.length === 0) {
    return (
      <div className="card">
        {showHeader && (
          <div className="card-header">
            <h3 className="font-semibold text-gray-800">{title}</h3>
          </div>
        )}
        <div className="card-body h-64 flex items-center justify-center text-gray-500">
          No hay datos disponibles
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {showHeader && (
        <div className="card-header">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className="card-body">
        <ResponsiveContainer width="100%" height={height}>
          <ComposedChart data={data} margin={{ top: 30, right: 60, left: 20, bottom: 5 }}>
            <XAxis 
              dataKey="period" 
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickFormatter={formatAxisCurrency}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickFormatter={formatAxisNumber}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value: string) => (
                <span className="text-xs text-gray-600">{value}</span>
              )}
            />
            <Bar
              yAxisId="left"
              dataKey="gross_gmv"
              fill="#00C3A5"
              name="Gross GMV"
              barSize={40}
            >
              <LabelList 
                dataKey="gross_gmv" 
                position="top" 
                content={(props: any) => <GMVLabel {...props} />}
              />
            </Bar>
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="gross_bookings"
              stroke="#374151"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: '#374151', r: 4 }}
              name="# Gross Monthly Ops"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

