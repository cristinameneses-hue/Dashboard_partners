import {
  LineChart,
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
  [key: string]: string | number;
}

interface LineChartComponentProps {
  data: DataPoint[];
  title: string;
  dataKey: string;
  color?: string;
  isCurrency?: boolean;
  suffix?: string;
  height?: number;
  showHeader?: boolean;
}

// Format numbers with thousands separator
function formatNumber(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 2
  }).format(num);
}

// Format currency
function formatCurrency(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(Math.round(num));
}

// Custom tooltip
const CustomTooltip = ({ active, payload, label, isCurrency, suffix }: any) => {
  if (active && payload && payload.length) {
    const value = payload[0].value;
    const formattedValue = isCurrency 
      ? formatCurrency(value) 
      : `${formatNumber(value)}${suffix || ''}`;
    
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-800 mb-1">{label}</p>
        <p className="text-green-600 font-medium">{formattedValue}</p>
      </div>
    );
  }
  return null;
};

// Custom label on data points
const CustomLabel = (props: any) => {
  const { x, y, value, isCurrency, suffix } = props;
  if (value === undefined || value === null) return null;
  
  const formattedValue = isCurrency 
    ? formatCurrency(value)
    : `${formatNumber(value)}${suffix || ''}`;
  
  return (
    <text
      x={x}
      y={y - 10}
      fill="#374151"
      textAnchor="middle"
      fontSize={10}
      fontWeight={500}
    >
      {formattedValue}
    </text>
  );
};

export default function LineChartComponent({ 
  data, 
  title, 
  dataKey, 
  color = '#22c55e',
  isCurrency = false,
  suffix = '',
  height = 280,
  showHeader = true
}: LineChartComponentProps) {
  return (
    <div className="card h-full flex flex-col">
      {showHeader && (
        <div className="card-header bg-gray-50">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className="card-body flex-1">
        <ResponsiveContainer width="100%" height={height}>
          <LineChart
            data={data}
            margin={{ top: 25, right: 30, left: 20, bottom: 5 }}
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
                if (isCurrency) {
                  if (value >= 1000) return `${Math.round(value / 1000)}K€`;
                  return `${value}€`;
                }
                return formatNumber(value);
              }}
            />
            <Tooltip content={<CustomTooltip isCurrency={isCurrency} suffix={suffix} />} />
            <Legend 
              wrapperStyle={{ paddingTop: 10 }}
              formatter={() => title.split(' ').slice(-2).join(' ')}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={{ fill: color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
              label={(props: any) => (
                <CustomLabel {...props} isCurrency={isCurrency} suffix={suffix} />
              )}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
