import { useMemo } from 'react';
import type { ShortageTimeSeriesPoint } from '../../types';

interface ShortageTimeSeriesTableProps {
  data: ShortageTimeSeriesPoint[];
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

// Format delta (with + sign for positive)
function formatDelta(num: number): string {
  const formatted = new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 0,
    signDisplay: 'exceptZero'
  }).format(Math.round(num));
  return formatted;
}

// Format delta currency (with + sign for positive)
function formatDeltaCurrency(num: number): string {
  const sign = num > 0 ? '+' : '';
  return sign + new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(Math.round(num));
}

// Get heatmap color for specific metrics
function getHeatmapColor(value: number, metric: string, allValues: number[]): string {
  // Only apply heatmap to specific metrics
  const positiveMetrics = ['gross_bookings', 'gross_gmv', 'active_pharmacies'];
  const negativeMetrics = ['pct_cancelled', 'pct_cancelled_gmv'];
  const deltaMetrics = ['delta_bookings', 'delta_gmv', 'pct_growth_bookings', 'pct_growth_gmv'];
  
  if (!positiveMetrics.includes(metric) && !negativeMetrics.includes(metric) && !deltaMetrics.includes(metric)) {
    return '';
  }
  
  if (allValues.length === 0) return '';
  
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min;
  
  if (range === 0) return '';
  
  const normalized = (value - min) / range;
  
  // For delta metrics - green for positive, red for negative
  if (deltaMetrics.includes(metric)) {
    if (value > 0) {
      if (normalized >= 0.6) return 'bg-green-200/70';
      return 'bg-green-100/60';
    } else if (value < 0) {
      if (normalized <= 0.4) return 'bg-red-200/70';
      return 'bg-red-100/60';
    }
    return '';
  }
  
  // For cancelled metrics (lower is better - reverse colors)
  if (negativeMetrics.includes(metric)) {
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

// Format growth percentage (with + sign for positive)
function formatGrowthPercent(num: number): string {
  const sign = num > 0 ? '+' : '';
  return `${sign}${num.toFixed(1)}%`;
}

// Row definitions - ordered as requested
const rows = [
  { key: 'total_pharmacies', label: '# Farmacias', format: formatNumber },
  { key: 'active_pharmacies', label: '# Fcias. activas', format: formatNumber },
  { key: 'sending_pharmacies', label: '# Fcias. >0 envíos', format: formatNumber },
  { key: 'receiving_pharmacies', label: '# Fcias. >0 recepciones', format: formatNumber },
  { key: 'pct_active', label: '% Fcias. activas', format: formatPercent },
  { key: 'pct_receiving', label: '% Fcias. >0 recepciones', format: formatPercent },
  { key: 'pct_sending', label: '% Fcias. >0 envíos', format: formatPercent },
  { key: 'gross_bookings', label: 'Orders brutas', format: formatNumber },
  { key: 'cancelled_bookings', label: 'Orders canceladas', format: formatNumber },
  { key: 'net_bookings', label: 'Orders netas', format: formatNumber },
  { key: 'pct_cancelled', label: '% Cancelaciones orders', format: formatPercent },
  { key: 'delta_bookings', label: '∆ Orders', format: formatDelta },
  { key: 'pct_growth_bookings', label: '% Crecimiento orders', format: formatGrowthPercent },
  { key: 'gross_gmv', label: 'GMV bruto', format: formatCurrency },
  { key: 'cancelled_gmv', label: 'GMV cancelado', format: formatCurrency },
  { key: 'net_gmv', label: 'GMV neto', format: formatCurrency },
  { key: 'pct_cancelled_gmv', label: '% Cancelación GMV', format: formatPercent },
  { key: 'delta_gmv', label: '∆ GMV', format: formatDeltaCurrency },
  { key: 'pct_growth_gmv', label: '% Crecimiento GMV', format: formatGrowthPercent },
];

export default function ShortageTimeSeriesTable({ data, groupBy, title }: ShortageTimeSeriesTableProps) {
  // Get all values for a specific metric (for heatmap calculation)
  const getMetricValues = (metric: string): number[] => {
    return data.map(d => (d as any)[metric] || 0);
  };

  const getGroupLabel = () => {
    switch (groupBy) {
      case 'week': return 'SEMANAL';
      case 'month': return 'MENSUAL';
      case 'quarter': return 'TRIMESTRAL';
      case 'year': return 'ANUAL';
      default: return 'MENSUAL';
    }
  };

  const getDeltaLabel = () => {
    switch (groupBy) {
      case 'week': return 'WoW';
      case 'month': return 'MoM';
      case 'quarter': return 'QoQ';
      case 'year': return 'YoY';
      default: return 'vs anterior';
    }
  };

  // Update delta and growth labels dynamically
  const dynamicRows = useMemo(() => {
    const deltaLabel = getDeltaLabel();
    return rows.map(row => {
      if (row.key === 'delta_bookings') {
        return { ...row, label: `∆ Orders (${deltaLabel})` };
      }
      if (row.key === 'delta_gmv') {
        return { ...row, label: `∆ GMV (${deltaLabel})` };
      }
      if (row.key === 'pct_growth_bookings') {
        return { ...row, label: `% Crecimiento orders (${deltaLabel})` };
      }
      if (row.key === 'pct_growth_gmv') {
        return { ...row, label: `% Crecimiento GMV (${deltaLabel})` };
      }
      return row;
    });
  }, [groupBy]);

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
              <th className="px-3 py-2 text-left font-semibold sticky left-0 bg-gray-700 z-10 min-w-[180px]">
                {getGroupLabel()}
              </th>
              {data.map((point, idx) => (
                <th key={idx} className="px-3 py-2 text-center font-semibold whitespace-nowrap min-w-[80px]">
                  {point.period}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dynamicRows.map((row) => {
              const metricValues = getMetricValues(row.key);
              
              return (
                <tr key={row.key} className="border-b border-gray-200 hover:bg-gray-50/50">
                  <td className="px-3 py-2 font-medium sticky left-0 z-10 bg-gray-100 text-gray-700">
                    {row.label}
                  </td>
                  {data.map((point, idx) => {
                    const value = (point as any)[row.key] || 0;
                    const cellBg = getHeatmapColor(value, row.key, metricValues);
                    
                    // Special styling for delta and growth values
                    let textColor = '';
                    const isDeltaOrGrowth = ['delta_bookings', 'delta_gmv', 'pct_growth_bookings', 'pct_growth_gmv'].includes(row.key);
                    if (isDeltaOrGrowth) {
                      if (value > 0) textColor = 'text-green-600 font-medium';
                      else if (value < 0) textColor = 'text-red-600 font-medium';
                    }
                    
                    return (
                      <td 
                        key={idx} 
                        className={`px-3 py-2 text-center whitespace-nowrap ${cellBg} ${textColor}`}
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

