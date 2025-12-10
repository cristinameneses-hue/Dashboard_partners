interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'blue' | 'green' | 'amber' | 'purple' | 'red' | 'cyan' | 'teal';
  size?: 'sm' | 'md' | 'lg';
}

const colorClasses = {
  blue: 'bg-blue-50 border-blue-200',
  green: 'bg-green-50 border-green-200',
  amber: 'bg-amber-50 border-amber-200',
  purple: 'bg-purple-50 border-purple-200',
  red: 'bg-red-50 border-red-200',
  cyan: 'bg-cyan-50 border-cyan-200',
  teal: 'bg-teal-50 border-teal-200',
};

const textColors = {
  blue: 'text-blue-700',
  green: 'text-green-700',
  amber: 'text-amber-700',
  purple: 'text-purple-700',
  red: 'text-red-700',
  cyan: 'text-cyan-700',
  teal: 'text-teal-700',
};

const iconColors = {
  blue: 'bg-blue-100',
  green: 'bg-green-100',
  amber: 'bg-amber-100',
  purple: 'bg-purple-100',
  red: 'bg-red-100',
  cyan: 'bg-cyan-100',
  teal: 'bg-teal-100',
};

const sizeClasses = {
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

const valueSizes = {
  sm: 'text-lg',
  md: 'text-2xl',
  lg: 'text-3xl',
};

export default function MetricCard({
  title,
  value,
  subtitle,
  color = 'blue',
  size = 'md',
}: MetricCardProps) {
  return (
    <div
      className={`rounded-xl ${colorClasses[color]} border ${sizeClasses[size]} transition-all hover:shadow-md`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
            {title}
          </p>
          <p className={`font-bold ${textColors[color]} ${valueSizes[size]}`}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`w-8 h-8 rounded-lg ${iconColors[color]} flex items-center justify-center`}>
          <div className={`w-2 h-2 rounded-full ${textColors[color].replace('text-', 'bg-')}`} />
        </div>
      </div>
    </div>
  );
}
