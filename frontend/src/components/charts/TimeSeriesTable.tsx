import { useMemo } from 'react';
import type { TimeSeriesPoint } from '../../types';

interface TimeSeriesTableProps {
  data: TimeSeriesPoint[];
  groupBy: string;
  title?: string;
}

// Format numbers with thousands separator
function formatNumber(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 0
  }).format(Math.round(num));
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

// Format percentage
function formatPercent(num: number): string {
  return `${num.toFixed(1)}%`;
}

// Format decimal
function formatDecimal(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    minimumFractionDigits: 1,
    maximumFractionDigits: 1
  }).format(num);
}

// Get cell background color based on value and metric type
function getCellColor(value: number, metric: string, allValues: number[]): string {
  if (allValues.length === 0) return '';
  
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min;
  
  if (range === 0) return '';
  
  const normalized = (value - min) / range;
  
  // For percentage metrics (higher is better except cancelled)
  if (metric === 'pct_pharmacies_active') {
    if (normalized >= 0.8) return 'bg-green-100';
    if (normalized >= 0.6) return 'bg-green-50';
    if (normalized <= 0.2) return 'bg-red-100';
    if (normalized <= 0.4) return 'bg-red-50';
    return '';
  }
  
  // For cancelled metrics (lower is better)
  if (metric.includes('cancelled') || metric.includes('cancel')) {
    if (normalized >= 0.8) return 'bg-red-100';
    if (normalized >= 0.6) return 'bg-red-50';
    if (normalized <= 0.2) return 'bg-green-100';
    if (normalized <= 0.4) return 'bg-green-50';
    return '';
  }
  
  // For regular metrics (higher is better)
  if (normalized >= 0.8) return 'bg-green-100';
  if (normalized >= 0.6) return 'bg-green-50';
  if (normalized <= 0.2) return 'bg-amber-100';
  if (normalized <= 0.4) return 'bg-amber-50';
  return '';
}

// Row definitions
const rows = [
  { key: 'total_pharmacies', label: '# Active Ph.', format: formatNumber, colorize: false },
  { key: 'pharmacies_with_orders', label: '# Ph. ≥1 order', format: formatNumber, colorize: true },
  { key: 'pct_pharmacies_active', label: '% Ph. ≥1 order', format: formatPercent, colorize: true },
  { key: 'gross_bookings', label: 'Total orders', format: formatNumber, colorize: true },
  { key: 'avg_orders_per_pharmacy', label: 'Avg. orders per Ph.', format: formatDecimal, colorize: true },
  { key: 'gross_gmv', label: 'Total GMV', format: formatCurrency, colorize: true },
  { key: 'avg_gmv_per_pharmacy', label: 'Avg. GMV per Ph.', format: formatCurrency, colorize: true },
  { key: 'cancelled_bookings', label: '# Cancelled orders', format: formatNumber, colorize: true },
  { key: 'pct_cancelled', label: '% Cancelled orders', format: formatPercent, colorize: true },
  { key: 'net_bookings', label: 'Net orders', format: formatNumber, colorize: true },
  { key: 'cancelled_gmv', label: '# Cancelled GMV', format: formatCurrency, colorize: true },
  { key: 'net_gmv', label: 'Net GMV', format: formatCurrency, colorize: true },
  { key: 'average_ticket', label: 'Avg. order value', format: formatCurrency, colorize: false },
];

// Row colors
const rowColors: Record<string, string> = {
  'total_pharmacies': 'bg-blue-600 text-white',
  'pharmacies_with_orders': 'bg-blue-500 text-white',
  'pct_pharmacies_active': 'bg-blue-400 text-white',
  'gross_bookings': 'bg-gray-100',
  'avg_orders_per_pharmacy': 'bg-gray-50',
  'gross_gmv': 'bg-amber-500 text-white',
  'avg_gmv_per_pharmacy': 'bg-amber-400 text-white',
  'cancelled_bookings': 'bg-gray-100',
  'pct_cancelled': 'bg-orange-500 text-white',
  'net_bookings': 'bg-gray-50',
  'cancelled_gmv': 'bg-amber-600 text-white',
  'net_gmv': 'bg-green-600 text-white',
  'average_ticket': 'bg-gray-100',
};

export default function TimeSeriesTable({ data, groupBy, title }: TimeSeriesTableProps) {
  // Calculate pct_cancelled for each data point
  const enrichedData = useMemo(() => {
    return data.map(point => ({
      ...point,
      pct_cancelled: point.gross_bookings > 0 
        ? (point.cancelled_bookings / point.gross_bookings) * 100 
        : 0
    }));
  }, [data]);

  // Get all values for a specific metric (for color calculation)
  const getMetricValues = (metric: string): number[] => {
    return enrichedData.map(d => (d as any)[metric] || 0);
  };

  const getGroupLabel = () => {
    switch (groupBy) {
      case 'week': return 'WEEKLY';
      case 'month': return 'MONTHLY';
      case 'quarter': return 'QUARTERLY';
      case 'year': return 'YEARLY';
      default: return 'MONTHLY';
    }
  };

  if (data.length === 0) {
    return (
      <div className="card">
        <div className="card-body text-center text-gray-500 py-8">
          No hay datos disponibles para mostrar
        </div>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      {title && (
        <div className="card-header bg-gray-50">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-700 text-white">
              <th className="px-3 py-2 text-left font-semibold sticky left-0 bg-gray-700 z-10 min-w-[140px]">
                {getGroupLabel()}
              </th>
              {enrichedData.map((point, idx) => (
                <th key={idx} className="px-3 py-2 text-center font-semibold whitespace-nowrap min-w-[80px]">
                  {point.period}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const metricValues = getMetricValues(row.key);
              const headerBgClass = rowColors[row.key] || 'bg-gray-100';
              
              return (
                <tr key={row.key} className="border-b border-gray-200 hover:bg-gray-50/50">
                  <td className={`px-3 py-2 font-medium sticky left-0 z-10 ${headerBgClass}`}>
                    {row.label}
                  </td>
                  {enrichedData.map((point, idx) => {
                    const value = (point as any)[row.key] || 0;
                    const cellBg = row.colorize ? getCellColor(value, row.key, metricValues) : '';
                    
                    return (
                      <td 
                        key={idx} 
                        className={`px-3 py-2 text-center whitespace-nowrap ${cellBg}`}
                      >
                        {row.format(value)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

