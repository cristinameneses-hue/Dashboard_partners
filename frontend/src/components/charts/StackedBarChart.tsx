import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';

interface TimeSeriesPoint {
  period: string;
  gross_bookings: number;
  cancelled_bookings: number;
  net_bookings: number;
  gross_gmv: number;
  cancelled_gmv: number;
  net_gmv: number;
}

interface StackedBarChartProps {
  data: TimeSeriesPoint[];
  title: string;
  type: 'bookings' | 'gmv';
}

// Format numbers with thousands separator
function formatNumber(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 0
  }).format(Math.round(num));
}

// Format currency without decimals
function formatGMV(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(Math.round(num));
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label, type }: any) => {
  if (active && payload && payload.length) {
    const formatter = type === 'gmv' ? formatGMV : formatNumber;
    const gross = payload.find((p: any) => p.dataKey === (type === 'gmv' ? 'net_gmv' : 'net_bookings'));
    const cancelled = payload.find((p: any) => p.dataKey === (type === 'gmv' ? 'cancelled_gmv' : 'cancelled_bookings'));
    
    const grossValue = gross?.value || 0;
    const cancelledValue = cancelled?.value || 0;
    const total = grossValue + cancelledValue;
    const pctCancelled = total > 0 ? ((cancelledValue / total) * 100).toFixed(1) : '0.0';
    
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-800 mb-2">{label}</p>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-gray-600">Total (Gross):</span>
            <span className="font-medium">{formatter(total)}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-green-600">Net:</span>
            <span className="font-medium text-green-600">{formatter(grossValue)}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-orange-500">Cancelled:</span>
            <span className="font-medium text-orange-500">{formatter(cancelledValue)}</span>
          </div>
          <div className="flex justify-between gap-4 pt-1 border-t border-gray-100">
            <span className="text-gray-500">% Cancel:</span>
            <span className="font-medium text-orange-500">{pctCancelled}%</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

// Custom label for total
const TotalLabel = (props: any) => {
  const { x, y, width, value, type, data, index } = props;
  if (!data || !data[index]) return null;
  
  const point = data[index];
  const total = type === 'gmv' 
    ? point.net_gmv + point.cancelled_gmv
    : point.net_bookings + point.cancelled_bookings;
  
  const formatter = type === 'gmv' ? formatGMV : formatNumber;
  
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      fill="#374151"
      textAnchor="middle"
      fontSize={11}
      fontWeight={600}
    >
      {formatter(total)}
    </text>
  );
};

export default function StackedBarChart({ data, title, type }: StackedBarChartProps) {
  const netKey = type === 'gmv' ? 'net_gmv' : 'net_bookings';
  const cancelledKey = type === 'gmv' ? 'cancelled_gmv' : 'cancelled_bookings';
  const formatter = type === 'gmv' ? formatGMV : formatNumber;
  
  return (
    <div className="card">
      <div className="card-header bg-gray-50">
        <h3 className="font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={350}>
          <BarChart
            data={data}
            margin={{ top: 30, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="period" 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={{ stroke: '#d1d5db' }}
            />
            <YAxis 
              tick={{ fontSize: 11, fill: '#6b7280' }}
              axisLine={{ stroke: '#d1d5db' }}
              tickFormatter={(value) => {
                if (type === 'gmv') {
                  if (value >= 1000) return `${Math.round(value / 1000)}K€`;
                  return `${value}€`;
                }
                if (value >= 1000) return `${Math.round(value / 1000)}K`;
                return value.toString();
              }}
            />
            <Tooltip content={<CustomTooltip type={type} />} />
            <Legend 
              wrapperStyle={{ paddingTop: 10 }}
              formatter={(value) => {
                if (value === netKey) return type === 'gmv' ? 'Net GMV' : 'Net Orders';
                if (value === cancelledKey) return type === 'gmv' ? 'Cancelled GMV' : 'Cancelled Orders';
                return value;
              }}
            />
            <Bar 
              dataKey={netKey} 
              stackId="a" 
              fill="#22c55e"
              name={netKey}
              radius={[0, 0, 0, 0]}
            />
            <Bar 
              dataKey={cancelledKey} 
              stackId="a" 
              fill="#f97316"
              name={cancelledKey}
              radius={[4, 4, 0, 0]}
            >
              <LabelList
                content={(props) => <TotalLabel {...props} type={type} data={data} />}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

