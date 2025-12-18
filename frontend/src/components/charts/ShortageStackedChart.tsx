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

interface ShortageStackedChartProps {
  data: ShortageTimeSeriesPoint[];
  title: string;
  type: 'ops' | 'gmv';
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

// Custom label for total on top of stacked bars
function TotalLabel({ x, y, width, value, type }: any) {
  if (!value || value === 0) return null;
  
  const formattedValue = type === 'gmv' 
    ? formatCurrency(value) 
    : formatNumber(value);
  
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      textAnchor="middle"
      fill="#374151"
      fontSize={10}
      fontWeight={600}
    >
      {formattedValue}
    </text>
  );
}

// Custom tooltip
function CustomTooltip({ active, payload, label, type }: any) {
  if (!active || !payload?.length) return null;

  const data = payload[0]?.payload;
  if (!data) return null;

  const gross = type === 'gmv' ? data.gross_gmv : data.gross_bookings;
  const cancelled = type === 'gmv' ? data.cancelled_gmv : data.cancelled_bookings;
  const net = type === 'gmv' ? data.net_gmv : data.net_bookings;
  const pct = type === 'gmv' ? data.pct_cancelled_gmv : data.pct_cancelled;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800 mb-2">{label}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Gross:</span>
          <span className="font-medium text-[#00C3A5]">
            {type === 'gmv' ? formatCurrency(gross) : formatNumber(gross)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Cancelled:</span>
          <span className="font-medium text-[#f59e0b]">
            {type === 'gmv' ? formatCurrency(cancelled) : formatNumber(cancelled)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Net:</span>
          <span className="font-medium text-[#0ea5e9]">
            {type === 'gmv' ? formatCurrency(net) : formatNumber(net)}
          </span>
        </div>
        <div className="flex justify-between gap-4 pt-1 border-t border-gray-200">
          <span className="text-gray-600">% Cancelled:</span>
          <span className="font-medium text-red-500">{pct.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}

export default function ShortageStackedChart({ data, title, type }: ShortageStackedChartProps) {
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

  // Prepare data with gross values for stacking
  const chartData = data.map(item => ({
    ...item,
    _gross: type === 'gmv' ? item.gross_gmv : item.gross_bookings,
  }));

  const netKey = type === 'gmv' ? 'net_gmv' : 'net_bookings';
  const cancelledKey = type === 'gmv' ? 'cancelled_gmv' : 'cancelled_bookings';
  const pctKey = type === 'gmv' ? 'pct_cancelled_gmv' : 'pct_cancelled';

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={chartData} margin={{ top: 30, right: 60, left: 20, bottom: 5 }}>
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
              tickFormatter={type === 'gmv' ? formatAxisCurrency : formatAxisNumber}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 50]}
              tick={{ fontSize: 11, fill: '#6B7280' }}
              tickLine={{ stroke: '#E5E7EB' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip type={type} />} />
            <Legend 
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value: string) => (
                <span className="text-xs text-gray-600">{value}</span>
              )}
            />
            <Bar
              yAxisId="left"
              dataKey={netKey}
              stackId="stack"
              fill="#0ea5e9"
              name={type === 'gmv' ? 'Net GMV' : 'Net Ops'}
            />
            <Bar
              yAxisId="left"
              dataKey={cancelledKey}
              stackId="stack"
              fill="#f59e0b"
              name={type === 'gmv' ? 'Cancelled GMV' : 'Cancelled Ops'}
            >
              <LabelList 
                dataKey="_gross" 
                position="top" 
                content={(props: any) => <TotalLabel {...props} type={type} />}
              />
            </Bar>
            <Line
              yAxisId="right"
              type="monotone"
              dataKey={pctKey}
              stroke="#ef4444"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: '#ef4444', r: 3 }}
              name="% Cancelled"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

