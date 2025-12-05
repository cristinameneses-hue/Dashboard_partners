import { useState, useMemo } from 'react';
import { createColumnHelper } from '@tanstack/react-table';
import FilterBar from '../components/FilterBar';
import MetricCard from '../components/MetricCard';
import DataTable from '../components/DataTable';
import BarChartComponent from '../components/charts/BarChartComponent';
import { useEcommerceMetrics } from '../hooks/useEcommerce';
import type { PeriodType, EcommerceMetrics } from '../types';
import { PARTNER_CATEGORIES, getCategoryByPartner } from '../types';

const columnHelper = createColumnHelper<EcommerceMetrics>();

// Format numbers with full representation (no abbreviations)
function formatNumber(num: number): string {
  return num.toLocaleString('es-ES');
}

function formatCurrency(num: number): string {
  return num.toLocaleString('es-ES', { 
    style: 'currency', 
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// Category metrics aggregation
interface CategoryMetrics {
  category: string;
  color: string;
  net_bookings: number;
  net_gmv: number;
  average_ticket: number;
  pct_cancelled: number;
  partners_count: number;
}

export default function Ecommerce() {
  const [periodType, setPeriodType] = useState<PeriodType>('this_month');
  const [customStart, setCustomStart] = useState<string>();
  const [customEnd, setCustomEnd] = useState<string>();
  const [selectedPartners, setSelectedPartners] = useState<string[]>([]);

  const { data, loading, error } = useEcommerceMetrics(
    periodType,
    customStart,
    customEnd
  );

  const handlePeriodChange = (
    period: PeriodType,
    start?: string,
    end?: string
  ) => {
    setPeriodType(period);
    if (period === 'custom') {
      if (start) setCustomStart(start);
      if (end) setCustomEnd(end);
    } else {
      setCustomStart(undefined);
      setCustomEnd(undefined);
    }
  };

  // Filter partners based on selection
  const filteredPartners = useMemo(() => {
    if (!data?.partners) return [];
    if (selectedPartners.length === 0) return data.partners;
    return data.partners.filter(p => 
      selectedPartners.includes(p.partner.toLowerCase())
    );
  }, [data?.partners, selectedPartners]);

  // Calculate category metrics
  const categoryMetrics = useMemo((): CategoryMetrics[] => {
    if (!data?.partners) return [];
    
    return PARTNER_CATEGORIES
      .filter(cat => cat.id !== 'all')
      .map(category => {
        const categoryPartners = data.partners.filter(p => 
          category.partners.includes(p.partner.toLowerCase())
        );
        
        const net_bookings = categoryPartners.reduce((sum, p) => sum + p.net_bookings, 0);
        const net_gmv = categoryPartners.reduce((sum, p) => sum + p.net_gmv, 0);
        const gross_bookings = categoryPartners.reduce((sum, p) => sum + p.gross_bookings, 0);
        const cancelled_bookings = categoryPartners.reduce((sum, p) => sum + p.cancelled_bookings, 0);
        
        return {
          category: category.name,
          color: category.color,
          net_bookings,
          net_gmv,
          average_ticket: net_bookings > 0 ? net_gmv / net_bookings : 0,
          pct_cancelled: gross_bookings > 0 ? (cancelled_bookings / gross_bookings) * 100 : 0,
          partners_count: categoryPartners.length,
        };
      })
      .filter(cat => cat.partners_count > 0);
  }, [data?.partners]);

  // Calculate filtered totals
  const filteredTotals = useMemo(() => {
    if (selectedPartners.length === 0) return data?.totals;
    
    const filtered = filteredPartners;
    if (filtered.length === 0) return null;

    const gross_bookings = filtered.reduce((sum, p) => sum + p.gross_bookings, 0);
    const cancelled_bookings = filtered.reduce((sum, p) => sum + p.cancelled_bookings, 0);
    const net_bookings = filtered.reduce((sum, p) => sum + p.net_bookings, 0);
    const gross_gmv = filtered.reduce((sum, p) => sum + p.gross_gmv, 0);
    const cancelled_gmv = filtered.reduce((sum, p) => sum + p.cancelled_gmv, 0);
    const net_gmv = filtered.reduce((sum, p) => sum + p.net_gmv, 0);
    const pharmacies = filtered.reduce((sum, p) => sum + p.pharmacies_with_orders, 0);

    return {
      gross_bookings,
      cancelled_bookings,
      net_bookings,
      gross_gmv,
      cancelled_gmv,
      net_gmv,
      average_ticket: net_bookings > 0 ? net_gmv / net_bookings : 0,
      avg_orders_per_pharmacy: pharmacies > 0 ? net_bookings / pharmacies : 0,
      avg_gmv_per_pharmacy: pharmacies > 0 ? net_gmv / pharmacies : 0,
      pct_cancelled_bookings: gross_bookings > 0 ? (cancelled_bookings / gross_bookings) * 100 : 0,
      pct_cancelled_gmv: gross_gmv > 0 ? (cancelled_gmv / gross_gmv) * 100 : 0,
    };
  }, [data?.totals, filteredPartners, selectedPartners]);

  const columns = useMemo(() => [
    columnHelper.accessor('partner', {
      header: 'Partner',
      cell: (info) => {
        const category = getCategoryByPartner(info.getValue());
        return (
          <div className="flex items-center gap-2">
            <div 
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: category?.color || '#64748b' }}
            />
            <span className="font-medium text-white capitalize">
              {info.getValue().replace('-', ' ')}
            </span>
          </div>
        );
      },
    }),
    columnHelper.accessor('net_bookings', {
      header: 'Net Bookings',
      cell: (info) => formatNumber(info.getValue()),
    }),
    columnHelper.accessor('net_gmv', {
      header: 'Net GMV',
      cell: (info) => (
        <span className="text-emerald-400 font-medium">
          {formatCurrency(info.getValue())}
        </span>
      ),
    }),
    columnHelper.accessor('average_ticket', {
      header: 'Avg Ticket',
      cell: (info) => formatCurrency(info.getValue()),
    }),
    columnHelper.accessor('pct_cancelled_bookings', {
      header: '% Cancelled',
      cell: (info) => (
        <span className={info.getValue() > 10 ? 'text-red-400' : 'text-slate-300'}>
          {info.getValue().toFixed(1)}%
        </span>
      ),
    }),
    columnHelper.accessor('pct_active_pharmacies', {
      header: '% Active Pharm.',
      cell: (info) => {
        const val = info.getValue();
        return val !== null ? `${val.toFixed(1)}%` : 'N/A';
      },
    }),
    columnHelper.accessor('pharmacies_with_orders', {
      header: 'Pharmacies',
      cell: (info) => formatNumber(info.getValue()),
    }),
  ], []);

  // Prepare chart data by category
  const gmvByCategoryData = useMemo(() => 
    categoryMetrics
      .sort((a, b) => b.net_gmv - a.net_gmv)
      .map(cat => ({
        name: cat.category,
        value: cat.net_gmv,
        fill: cat.color
      })),
    [categoryMetrics]
  );

  // Prepare chart data by partner
  const gmvChartData = useMemo(() => 
    filteredPartners
      .sort((a, b) => b.net_gmv - a.net_gmv)
      .slice(0, 10)
      .map(p => {
        const category = getCategoryByPartner(p.partner);
        return {
          name: p.partner.replace('-', ' '),
          value: p.net_gmv,
          fill: category?.color || '#64748b'
        };
      }),
    [filteredPartners]
  );

  const bookingsChartData = useMemo(() =>
    filteredPartners
      .sort((a, b) => b.net_bookings - a.net_bookings)
      .slice(0, 10)
      .map(p => {
        const category = getCategoryByPartner(p.partner);
        return {
          name: p.partner.replace('-', ' '),
          value: p.net_bookings,
          fill: category?.color || '#64748b'
        };
      }),
    [filteredPartners]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-xl text-slate-400">Cargando métricas...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl text-red-400">{error}</div>
      </div>
    );
  }

  const totals = filteredTotals;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Ecommerce Metrics
          </h1>
          <p className="text-slate-400">
            Métricas de rendimiento por partner y categoría
          </p>
        </div>
        {data && (
          <div className="text-right">
            <p className="text-xs text-slate-500">Período</p>
            <p className="text-sm text-slate-300">
              {new Date(data.period_start).toLocaleDateString('es-ES')} - {new Date(data.period_end).toLocaleDateString('es-ES')}
            </p>
          </div>
        )}
      </div>

      {/* Filter Bar */}
      <div className="card p-4 animate-fade-in stagger-1 relative" style={{ zIndex: 100 }}>
        <FilterBar
          periodType={periodType}
          onPeriodChange={handlePeriodChange}
          customStart={customStart}
          customEnd={customEnd}
          selectedPartners={selectedPartners}
          onPartnersChange={setSelectedPartners}
        />
      </div>

      {/* Category Summary Cards */}
      {selectedPartners.length === 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 animate-fade-in stagger-2">
          {categoryMetrics.map((cat) => (
            <div 
              key={cat.category}
              className="card p-4 cursor-pointer hover:border-white/20 transition-all group"
              onClick={() => {
                const categoryInfo = PARTNER_CATEGORIES.find(c => c.name === cat.category);
                if (categoryInfo) {
                  setSelectedPartners(categoryInfo.partners);
                }
              }}
            >
              <div className="flex items-center gap-2 mb-3">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: cat.color }}
                />
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                  {cat.category}
                </span>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-bold" style={{ color: cat.color }}>
                  {formatCurrency(cat.net_gmv)}
                </p>
                <p className="text-xs text-slate-500">
                  {formatNumber(cat.net_bookings)} bookings
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-white/5">
                <p className="text-xs text-slate-500">
                  {cat.partners_count} partner{cat.partners_count > 1 ? 's' : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* KPI Summary */}
      {totals && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 animate-fade-in stagger-2">
          <MetricCard
            title="Gross Bookings"
            value={formatNumber(totals.gross_bookings)}
            color="blue"
          />
          <MetricCard
            title="Net Bookings"
            value={formatNumber(totals.net_bookings)}
            color="green"
          />
          <MetricCard
            title="Gross GMV"
            value={formatCurrency(totals.gross_gmv)}
            color="amber"
          />
          <MetricCard
            title="Net GMV"
            value={formatCurrency(totals.net_gmv)}
            color="green"
          />
          <MetricCard
            title="Avg Ticket"
            value={formatCurrency(totals.average_ticket)}
            color="purple"
          />
          <MetricCard
            title="% Cancelled"
            value={`${totals.pct_cancelled_bookings.toFixed(1)}%`}
            color="red"
          />
        </div>
      )}

      {/* Cancelled Metrics Row */}
      {totals && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in stagger-3">
          <MetricCard
            title="Cancelled Bookings"
            value={formatNumber(totals.cancelled_bookings)}
            color="red"
            size="sm"
          />
          <MetricCard
            title="Cancelled GMV"
            value={formatCurrency(totals.cancelled_gmv)}
            color="red"
            size="sm"
          />
          <MetricCard
            title="Avg Orders/Pharmacy"
            value={totals.avg_orders_per_pharmacy.toFixed(1)}
            color="cyan"
            size="sm"
          />
          <MetricCard
            title="Avg GMV/Pharmacy"
            value={formatCurrency(totals.avg_gmv_per_pharmacy)}
            color="cyan"
            size="sm"
          />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in stagger-4">
        {selectedPartners.length === 0 ? (
          <>
            <BarChartComponent
              data={gmvByCategoryData}
              title="Net GMV por Categoría"
              color="#10b981"
              useCustomColors
            />
            <BarChartComponent
              data={gmvChartData}
              title="Net GMV por Partner"
              color="#10b981"
              useCustomColors
            />
          </>
        ) : (
          <>
            <BarChartComponent
              data={gmvChartData}
              title="Net GMV por Partner"
              color="#10b981"
              useCustomColors
            />
            <BarChartComponent
              data={bookingsChartData}
              title="Net Bookings por Partner"
              color="#0ea5e9"
              useCustomColors
            />
          </>
        )}
      </div>

      {/* Partners Table */}
      <div className="card animate-fade-in">
        <div className="card-header flex items-center justify-between">
          <h3 className="font-semibold text-white">
            {selectedPartners.length > 0 
              ? `Partners Seleccionados (${filteredPartners.length})`
              : 'Todos los Partners'
            }
          </h3>
          {selectedPartners.length > 0 && (
            <button
              onClick={() => setSelectedPartners([])}
              className="text-xs text-slate-400 hover:text-white transition-colors"
            >
              Ver todos
            </button>
          )}
        </div>
        <div className="card-body">
          <DataTable
            data={filteredPartners}
            columns={columns}
            pageSize={12}
          />
        </div>
      </div>
    </div>
  );
}
