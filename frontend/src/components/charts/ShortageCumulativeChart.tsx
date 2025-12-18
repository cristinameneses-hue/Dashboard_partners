import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
  Cell,
} from 'recharts';
import type { ShortageTimeSeriesPoint } from '../../types';

interface ShortageCumulativeChartProps {
  data: ShortageTimeSeriesPoint[];
  title: string;
  type: 'ops' | 'gmv';
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

// Custom label for value on top of bars
function ValueLabel({ x, y, width, value, type }: any) {
  if (!value || value === 0) return null;
  
  const formattedValue = type === 'gmv' 
    ? formatCurrency(value) 
    : formatNumber(value);
  
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      textAnchor="middle"
      fill="#00A651"
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

  const value = type === 'gmv' ? data.cumulative_gmv : data.cumulative_ops;
  const periodValue = type === 'gmv' ? data.gross_gmv : data.gross_bookings;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 text-sm">
      <p className="font-semibold text-gray-800 mb-2">{label}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Período:</span>
          <span className="font-medium text-gray-800">
            {type === 'gmv' ? formatCurrency(periodValue) : formatNumber(periodValue)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-600">Acumulado:</span>
          <span className="font-medium text-[#00A651]">
            {type === 'gmv' ? formatCurrency(value) : formatNumber(value)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ShortageCumulativeChart({ 
  data, 
  title, 
  type,
  height = 320,
  showHeader = true 
}: ShortageCumulativeChartProps) {
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

  const dataKey = type === 'gmv' ? 'cumulative_gmv' : 'cumulative_ops';

  // Generate gradient colors from light to dark teal
  const getBarColor = (index: number, total: number) => {
    const startLightness = 75;
    const endLightness = 40;
    const lightness = startLightness - ((startLightness - endLightness) * (index / (total - 1)));
    return `hsl(168, 76%, ${lightness}%)`;
  };

  return (
    <div className="card">
      {showHeader && (
        <div className="card-header">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className="card-body">
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} margin={{ top: 30, right: 30, left: 20, bottom: 5 }}>
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
              tickFormatter={type === 'gmv' ? formatAxisCurrency : formatAxisNumber}
            />
            <Tooltip content={<CustomTooltip type={type} />} />
            <Bar
              dataKey={dataKey}
              name={type === 'gmv' ? 'GMV Acumulado' : 'Ops Acumuladas'}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(index, data.length)} />
              ))}
              <LabelList 
                dataKey={dataKey} 
                position="top" 
                content={(props: any) => <ValueLabel {...props} type={type} />}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

