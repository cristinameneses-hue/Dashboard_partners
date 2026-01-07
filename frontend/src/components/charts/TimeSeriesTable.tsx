import { useMemo } from 'react';
import type { TimeSeriesPoint } from '../../types';

interface TimeSeriesTableProps {
  data: TimeSeriesPoint[];
  groupBy: string;
  title?: string;
  isExpanded?: boolean;
  showHeader?: boolean;
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

// Get heatmap color for specific metrics - softer, more transparent colors
function getHeatmapColor(value: number, metric: string, allValues: number[]): string {
  // Only apply heatmap to specific metrics
  const heatmapMetrics = ['gross_bookings', 'gross_gmv', 'pct_cancelled', 'pct_cancelled_gmv'];
  if (!heatmapMetrics.includes(metric)) return '';
  
  if (allValues.length === 0) return '';
  
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min;
  
  if (range === 0) return '';
  
  const normalized = (value - min) / range;
  
  // For cancelled metrics (lower is better - reverse colors)
  if (metric === 'pct_cancelled' || metric === 'pct_cancelled_gmv') {
    if (normalized >= 0.8) return 'bg-red-200/70';
    if (normalized >= 0.6) return 'bg-red-100/60';
    if (normalized >= 0.4) return 'bg-yellow-100/50';
    if (normalized >= 0.2) return 'bg-green-100/60';
    return 'bg-green-200/70';
  }
  
  // For positive metrics (higher is better - green for high values)
  if (normalized >= 0.8) return 'bg-green-200/70';
  if (normalized >= 0.6) return 'bg-green-100/60';
  if (normalized >= 0.4) return 'bg-yellow-100/50';
  if (normalized >= 0.2) return 'bg-red-100/60';
  return 'bg-red-200/70';
}

// Row definitions - ordered as requested
const rows = [
  { key: 'total_pharmacies', label: '# Farmacias', format: formatNumber },
  { key: 'pharmacies_with_orders', label: '# Fcias. ≥1 ped.', format: formatNumber },
  { key: 'pct_pharmacies_active', label: '% Fcias. ≥1 ped.', format: formatPercent },
  { key: 'gross_bookings', label: 'Total orders', format: formatNumber },
  { key: 'cancelled_bookings', label: 'Cancelled orders', format: formatNumber },
  { key: 'pct_cancelled', label: '% Cancelled orders', format: formatPercent },
  { key: 'net_bookings', label: 'Net orders', format: formatNumber },
  { key: 'gross_gmv', label: 'Total GMV', format: formatCurrency },
  { key: 'cancelled_gmv', label: 'Cancelled GMV', format: formatCurrency },
  { key: 'pct_cancelled_gmv', label: '% Cancelled GMV', format: formatPercent },
  { key: 'net_gmv', label: 'Net GMV', format: formatCurrency },
  { key: 'avg_orders_per_pharmacy', label: 'Avg. orders per Ph.', format: formatDecimal },
  { key: 'avg_gmv_per_pharmacy', label: 'Avg. GMV per Ph.', format: formatCurrency },
  { key: 'average_ticket', label: 'Avg. order value', format: formatCurrency },
];

export default function TimeSeriesTable({ data, groupBy, title, isExpanded = false, showHeader = true }: TimeSeriesTableProps) {
  // Calculate pct_cancelled and pct_cancelled_gmv for each data point
  const enrichedData = useMemo(() => {
    return data.map(point => ({
      ...point,
      pct_cancelled: point.gross_bookings > 0 
        ? (point.cancelled_bookings / point.gross_bookings) * 100 
        : 0,
      pct_cancelled_gmv: point.gross_gmv > 0
        ? (point.cancelled_gmv / point.gross_gmv) * 100
        : 0
    }));
  }, [data]);

  // Get all values for a specific metric (for heatmap calculation)
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
    <div className={`card overflow-hidden ${isExpanded ? 'border-0 shadow-none' : ''}`}>
      {title && showHeader && (
        <div className="card-header bg-gray-50">
          <h3 className="font-semibold text-gray-800">{title}</h3>
        </div>
      )}
      <div className={`overflow-x-auto ${isExpanded ? 'overflow-visible' : ''}`}>
        <table className={`w-full ${isExpanded ? 'text-base' : 'text-sm'}`}>
          <thead>
            <tr className="bg-gray-700 text-white">
              <th className="px-3 py-2 text-left font-semibold sticky left-0 bg-gray-700 z-10 min-w-[160px]">
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
              
              return (
                <tr key={row.key} className="border-b border-gray-200 hover:bg-gray-50/50">
                  <td className="px-3 py-2 font-medium sticky left-0 z-10 bg-gray-100 text-gray-700">
                    {row.label}
                  </td>
                  {enrichedData.map((point, idx) => {
                    const value = (point as any)[row.key] || 0;
                    const cellBg = getHeatmapColor(value, row.key, metricValues);
                    
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
