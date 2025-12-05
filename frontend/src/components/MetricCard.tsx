interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'blue' | 'green' | 'amber' | 'purple' | 'red' | 'cyan';
  size?: 'sm' | 'md' | 'lg';
}

const colorClasses = {
  blue: 'from-sky-500/20 to-sky-600/5 border-sky-500/20',
  green: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
  amber: 'from-amber-500/20 to-amber-600/5 border-amber-500/20',
  purple: 'from-purple-500/20 to-purple-600/5 border-purple-500/20',
  red: 'from-red-500/20 to-red-600/5 border-red-500/20',
  cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/20',
};

const textColors = {
  blue: 'text-sky-400',
  green: 'text-emerald-400',
  amber: 'text-amber-400',
  purple: 'text-purple-400',
  red: 'text-red-400',
  cyan: 'text-cyan-400',
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
      className={`rounded-xl bg-gradient-to-br ${colorClasses[color]} border backdrop-blur-sm ${sizeClasses[size]}`}
    >
      <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
        {title}
      </p>
      <p className={`font-bold ${textColors[color]} ${valueSizes[size]}`}>
        {value}
      </p>
      {subtitle && (
        <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
      )}
    </div>
  );
}
