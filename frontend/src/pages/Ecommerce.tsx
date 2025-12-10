import { useState, useMemo } from 'react';
import { createColumnHelper } from '@tanstack/react-table';
import FilterBar from '../components/FilterBar';
import MetricCard from '../components/MetricCard';
import DataTable from '../components/DataTable';
import StackedBarChart from '../components/charts/StackedBarChart';
import LineChartComponent from '../components/charts/LineChartComponent';
import PharmacyComboChart from '../components/charts/PharmacyComboChart';
import { useEcommerceMetrics, useTimeSeries, ChartGroupBy } from '../hooks/useEcommerce';
import type { PeriodType, EcommerceMetrics } from '../types';
import { PARTNER_CATEGORIES, getCategoryByPartner } from '../types';

const columnHelper = createColumnHelper<EcommerceMetrics>();

// Format numbers with thousands separator (punto de miles)
function formatNumber(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    useGrouping: true,
    maximumFractionDigits: 0
  }).format(Math.round(num));
}

// Format currency with decimals (for average ticket, etc.)
function formatCurrency(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    useGrouping: true
  }).format(num);
}

// Format GMV without decimals (rounded)
function formatGMV(num: number): string {
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
    useGrouping: true
  }).format(Math.round(num));
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

const CHART_GROUP_OPTIONS: { value: ChartGroupBy; label: string }[] = [
  { value: 'week', label: 'Semana' },
  { value: 'month', label: 'Mes' },
  { value: 'quarter', label: 'Trimestre' },
  { value: 'year', label: 'Año' },
];

export default function Ecommerce() {
  const [periodType, setPeriodType] = useState<PeriodType>('this_month');
  const [customStart, setCustomStart] = useState<string>();
  const [customEnd, setCustomEnd] = useState<string>();
  const [selectedPartners, setSelectedPartners] = useState<string[]>([]);
  const [chartGroupBy, setChartGroupBy] = useState<ChartGroupBy>('month');

  const { data, loading, error } = useEcommerceMetrics(
    periodType,
    customStart,
    customEnd
  );

  // Time series for charts - use this_year by default for charts
  const chartPeriodType = periodType === 'custom' ? 'custom' : 'this_year';
  const { data: timeSeriesData } = useTimeSeries(
    chartPeriodType,
    chartGroupBy,
    selectedPartners.length > 0 ? selectedPartners : undefined,
    periodType === 'custom' ? customStart : undefined,
    periodType === 'custom' ? customEnd : undefined
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
          {formatGMV(info.getValue())}
        </span>
      ),
    }),
    columnHelper.accessor('average_ticket', {
      header: 'Avg Ticket',
      cell: (info) => formatCurrency(info.getValue()),
    }),
    columnHelper.accessor('pct_cancelled_bookings', {
      header: '% Cancel Ops',
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-[#00A651] border-t-transparent rounded-full animate-spin"></div>
          <div className="text-xl text-gray-500">Cargando métricas...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-xl text-red-600">{error}</div>
      </div>
    );
  }

  const totals = filteredTotals;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Ecommerce Metrics
          </h1>
          <p className="text-gray-500">
            Métricas de rendimiento por partner y categoría
          </p>
        </div>
        {data && (
          <div className="text-right bg-white rounded-lg px-4 py-2 shadow-sm border border-gray-200">
            <p className="text-xs text-gray-400">Período</p>
            <p className="text-sm text-gray-700 font-medium">
              {new Date(data.period_start).toLocaleDateString('es-ES')} - {new Date(data.period_end).toLocaleDateString('es-ES')}
            </p>
          </div>
        )}
      </div>

      {/* Filter Bar - Sticky */}
      <div className="sticky top-0 z-50 -mx-8 px-8 py-3 bg-gray-50/95 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="card p-4" style={{ zIndex: 100 }}>
          <FilterBar
            periodType={periodType}
            onPeriodChange={handlePeriodChange}
            customStart={customStart}
            customEnd={customEnd}
            selectedPartners={selectedPartners}
            onPartnersChange={setSelectedPartners}
          />
        </div>
      </div>

      {/* Category Summary Cards */}
      {selectedPartners.length === 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 animate-fade-in stagger-2">
          {categoryMetrics.map((cat) => (
            <div 
              key={cat.category}
              className="bg-white rounded-xl p-4 cursor-pointer border border-gray-200 hover:border-green-300 hover:shadow-lg transition-all group"
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
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {cat.category}
                </span>
              </div>
              <div className="space-y-1">
                <p className="text-lg font-bold" style={{ color: cat.color }}>
                  {formatGMV(cat.net_gmv)}
                </p>
                <p className="text-xs text-gray-500">
                  {formatNumber(cat.net_bookings)} bookings
                </p>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-400">
                  {cat.partners_count} partner{cat.partners_count > 1 ? 's' : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* KPI Summary */}
      {totals && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 animate-fade-in stagger-2">
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
            value={formatGMV(totals.gross_gmv)}
            color="amber"
          />
          <MetricCard
            title="Net GMV"
            value={formatGMV(totals.net_gmv)}
            color="green"
          />
          <MetricCard
            title="Avg Ticket"
            value={formatCurrency(totals.average_ticket)}
            color="purple"
          />
          <MetricCard
            title="% Cancel Ops"
            value={`${totals.pct_cancelled_bookings.toFixed(1)}%`}
            color="red"
          />
          <MetricCard
            title="% Cancel GMV"
            value={`${totals.pct_cancelled_gmv.toFixed(1)}%`}
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
            value={formatGMV(totals.cancelled_gmv)}
            color="red"
            size="sm"
          />
          <MetricCard
            title="Avg Orders/Pharmacy"
            value={formatNumber(totals.avg_orders_per_pharmacy)}
            color="cyan"
            size="sm"
          />
          <MetricCard
            title="Avg GMV/Pharmacy"
            value={formatGMV(totals.avg_gmv_per_pharmacy)}
            color="cyan"
            size="sm"
          />
        </div>
      )}

      {/* Chart Time Filter */}
      <div className="flex items-center gap-4 animate-fade-in stagger-4">
        <span className="text-sm font-medium text-gray-600">Agrupar por:</span>
        <div className="flex gap-2">
          {CHART_GROUP_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setChartGroupBy(option.value)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                chartGroupBy === option.value
                  ? 'bg-green-600 text-white shadow-md'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-green-300 hover:bg-green-50'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-400 ml-2">
          (Datos del año actual{selectedPartners.length > 0 ? ` • ${selectedPartners.length} partner(s) seleccionado(s)` : ''})
        </span>
      </div>

      {/* Stacked Bar Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in stagger-4">
        <StackedBarChart
          data={timeSeriesData?.data || []}
          title="# Orders Gross, Net & Cancelled"
          type="bookings"
        />
        <StackedBarChart
          data={timeSeriesData?.data || []}
          title="€ GMV Gross, Net & Cancelled"
          type="gmv"
        />
      </div>

      {/* Line Charts - Averages */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in stagger-4">
        <LineChartComponent
          data={timeSeriesData?.data || []}
          title="Avg. orders per pharmacy"
          dataKey="avg_orders_per_pharmacy"
          color="#22c55e"
        />
        <LineChartComponent
          data={timeSeriesData?.data || []}
          title="Avg. GMV per pharmacy"
          dataKey="avg_gmv_per_pharmacy"
          color="#22c55e"
          isCurrency
        />
      </div>

      {/* More Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in stagger-4">
        <LineChartComponent
          data={timeSeriesData?.data || []}
          title="Avg. order value (Ticket medio)"
          dataKey="average_ticket"
          color="#22c55e"
          isCurrency
        />
        <PharmacyComboChart
          data={timeSeriesData?.data || []}
          title="Pharmacies with orders"
        />
      </div>

      {/* Partners Table */}
      <div className="card animate-fade-in">
        <div className="card-header flex items-center justify-between bg-gray-50">
          <h3 className="font-semibold text-gray-800">
            {selectedPartners.length > 0 
              ? `Partners Seleccionados (${filteredPartners.length})`
              : 'Todos los Partners'
            }
          </h3>
          {selectedPartners.length > 0 && (
            <button
              onClick={() => setSelectedPartners([])}
              className="text-xs text-green-600 hover:text-green-700 font-medium transition-colors"
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
