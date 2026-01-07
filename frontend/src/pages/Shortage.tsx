import { useState } from 'react';
import FilterBar from '../components/FilterBar';
import MetricCard from '../components/MetricCard';
import ExpandableChart from '../components/charts/ExpandableChart';
import ShortageStackedChart from '../components/charts/ShortageStackedChart';
import ShortageCumulativeChart from '../components/charts/ShortageCumulativeChart';
import ShortageOpsGMVCombo from '../components/charts/ShortageOpsGMVCombo';
import ShortageTimeSeriesTable from '../components/charts/ShortageTimeSeriesTable';
import { useShortageMetrics, useShortageTimeSeries, ChartGroupBy } from '../hooks/useShortage';
import type { PeriodType } from '../types';

// Time group options
const CHART_GROUP_OPTIONS: { value: ChartGroupBy; label: string }[] = [
  { value: 'week', label: 'Semana' },
  { value: 'month', label: 'Mes' },
  { value: 'quarter', label: 'Trimestre' },
  { value: 'year', label: 'Año' },
];

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

export default function Shortage() {
  const [periodType, setPeriodType] = useState<PeriodType>('this_month');
  const [customStart, setCustomStart] = useState<string>();
  const [customEnd, setCustomEnd] = useState<string>();
  const [chartGroupBy, setChartGroupBy] = useState<ChartGroupBy>('month');
  const [tableGroupBy, setTableGroupBy] = useState<ChartGroupBy>('month');

  // Period type for charts - respect the selected period for historical data
  const getChartPeriodType = (): PeriodType => {
    if (periodType === 'custom') return 'custom';
    if (periodType === 'last_year') return 'last_year';
    if (periodType === 'this_year') return 'this_year';
    // For other periods (today, yesterday, week, month, quarter), show current year trends
    return 'this_year';
  };
  
  const chartPeriodType = getChartPeriodType();

  const { data, loading, error } = useShortageMetrics(
    periodType,
    customStart,
    customEnd
  );

  const { data: timeSeriesData } = useShortageTimeSeries(
    chartPeriodType,
    chartGroupBy,
    periodType === 'custom' ? customStart : undefined,
    periodType === 'custom' ? customEnd : undefined
  );

  // Separate time series data for the table - use selected period for historical data
  const tablePeriodType = periodType === 'last_year' ? 'last_year' : chartPeriodType;
  const { data: tableTimeSeriesData } = useShortageTimeSeries(
    tablePeriodType,
    tableGroupBy,
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

  const metrics = data?.metrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          Shortage Metrics
        </h1>
        <p className="text-gray-500">
          Métricas de transferencias internas entre farmacias
        </p>
      </div>

      {/* Sticky Filter Bar with Period */}
      <div className="sticky top-0 z-50 -mx-8 px-8 py-3 bg-gray-50/95 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="card p-4" style={{ zIndex: 100 }}>
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <FilterBar
                periodType={periodType}
                onPeriodChange={handlePeriodChange}
                customStart={customStart}
                customEnd={customEnd}
                selectedPartners={[]}
                onPartnersChange={() => {}}
                showPartnerFilter={false}
              />
            </div>
            {data && (
              <div className="text-right bg-white rounded-lg px-4 py-2 shadow-sm border border-gray-200 flex-shrink-0">
                <p className="text-xs text-gray-400">Período seleccionado</p>
                <p className="text-sm text-gray-700 font-medium">
                  {new Date(data.period_start).toLocaleDateString('es-ES')} - {new Date(data.period_end).toLocaleDateString('es-ES')}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main KPIs */}
      {metrics && (
        <>
          {/* Bookings Metrics */}
          <div className="animate-fade-in stagger-2">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Bookings</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <MetricCard
                title="Gross Bookings"
                value={formatNumber(metrics.gross_bookings)}
                color="blue"
              />
              <MetricCard
                title="Cancelled"
                value={formatNumber(metrics.cancelled_bookings)}
                color="red"
              />
              <MetricCard
                title="Net Bookings"
                value={formatNumber(metrics.net_bookings)}
                color="green"
              />
              <MetricCard
                title="% Cancel Ops"
                value={`${metrics.pct_cancelled_bookings.toFixed(1)}%`}
                color="red"
              />
              <MetricCard
                title="Avg Orders/Pharm"
                value={formatNumber(metrics.avg_orders_per_pharmacy)}
                color="cyan"
              />
              <MetricCard
                title="Avg Ticket"
                value={formatCurrency(metrics.average_ticket)}
                color="purple"
              />
            </div>
          </div>

          {/* GMV Metrics */}
          <div className="animate-fade-in stagger-3">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">GMV</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <MetricCard
                title="Gross GMV"
                value={formatGMV(metrics.gross_gmv)}
                color="amber"
              />
              <MetricCard
                title="Cancelled GMV"
                value={formatGMV(metrics.cancelled_gmv)}
                color="red"
              />
              <MetricCard
                title="Net GMV"
                value={formatGMV(metrics.net_gmv)}
                color="green"
                size="lg"
              />
              <MetricCard
                title="% Cancel GMV"
                value={`${metrics.pct_cancelled_gmv.toFixed(1)}%`}
                color="red"
              />
              <MetricCard
                title="Avg GMV/Pharm"
                value={formatGMV(metrics.avg_gmv_per_pharmacy)}
                color="cyan"
              />
            </div>
          </div>

          {/* Pharmacy Metrics */}
          <div className="animate-fade-in stagger-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Farmacias</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-6 border border-green-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                      Farmacias Activas
                    </p>
                    <p className="text-3xl font-bold text-green-600">
                      {formatNumber(metrics.active_pharmacies)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Total con active=1</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                    <span className="text-2xl">◉</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 border border-amber-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                      Farmacias Emisoras
                    </p>
                    <p className="text-3xl font-bold text-amber-600">
                      {formatNumber(metrics.sending_pharmacies)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Mín. 1 shortage enviado</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
                    <span className="text-2xl">↑</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 border border-blue-200 shadow-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
                      Farmacias Receptoras
                    </p>
                    <p className="text-3xl font-bold text-blue-600">
                      {formatNumber(metrics.receiving_pharmacies)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">Mín. 1 shortage recibido</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-2xl">↓</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Charts Section */}
      <div className="space-y-6 animate-fade-in">
        {/* Time Group Filter */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">📈 Evolución Temporal</h2>
          <div className="flex items-center gap-2 bg-white rounded-lg p-1 border border-gray-200">
            {CHART_GROUP_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setChartGroupBy(option.value)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  chartGroupBy === option.value
                    ? 'bg-[#00A651] text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Ops & GMV Combined Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExpandableChart 
            title="Shortage Ops Monthly Evolution" 
            dataPoints={timeSeriesData?.data?.length || 12}
          >
            <ShortageStackedChart
              data={timeSeriesData?.data || []}
              title="Shortage Ops Monthly Evolution"
              type="ops"
            />
          </ExpandableChart>
          
          <ExpandableChart 
            title="Shortage GMV Monthly Evolution" 
            dataPoints={timeSeriesData?.data?.length || 12}
          >
            <ShortageStackedChart
              data={timeSeriesData?.data || []}
              title="Shortage GMV Monthly Evolution"
              type="gmv"
            />
          </ExpandableChart>
        </div>

        {/* Cumulative Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExpandableChart 
            title="Cumulated Shortage Ops" 
            dataPoints={timeSeriesData?.data?.length || 12}
          >
            <ShortageCumulativeChart
              data={timeSeriesData?.data || []}
              title="Cumulated Shortage Ops"
              type="ops"
            />
          </ExpandableChart>
          
          <ExpandableChart 
            title="Cumulated Shortage GMV" 
            dataPoints={timeSeriesData?.data?.length || 12}
          >
            <ShortageCumulativeChart
              data={timeSeriesData?.data || []}
              title="Cumulated Shortage GMV"
              type="gmv"
            />
          </ExpandableChart>
        </div>

        {/* Ops & GMV Combined Chart */}
        <ExpandableChart 
          title="Shortage Ops & GMV Monthly Evolution" 
          dataPoints={timeSeriesData?.data?.length || 12}
        >
          <ShortageOpsGMVCombo
            data={timeSeriesData?.data || []}
            title="Shortage Ops & GMV Monthly Evolution"
          />
        </ExpandableChart>
      </div>

      {/* Data Table Section */}
      <div className="space-y-4 animate-fade-in">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">📊 Tabla de Datos</h2>
          <div className="flex items-center gap-2 bg-white rounded-lg p-1 border border-gray-200">
            {CHART_GROUP_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setTableGroupBy(option.value)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  tableGroupBy === option.value
                    ? 'bg-[#00A651] text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
        
        {tableTimeSeriesData?.data && (
          <ShortageTimeSeriesTable
            data={tableTimeSeriesData.data}
            groupBy={tableGroupBy}
            title="Métricas de Shortage"
          />
        )}
      </div>

      {/* Summary Card */}
      {metrics && (
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm animate-fade-in">
          <h3 className="font-semibold text-gray-800 mb-4">Resumen</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-500">Total Transferencias</p>
              <p className="text-xl font-bold text-gray-800">
                {formatNumber(metrics.net_bookings)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Valor Total</p>
              <p className="text-xl font-bold text-green-600">
                {formatGMV(metrics.net_gmv)}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Tasa de Cancelación</p>
              <p className={`text-xl font-bold ${metrics.pct_cancelled_bookings > 10 ? 'text-red-600' : 'text-gray-800'}`}>
                {metrics.pct_cancelled_bookings.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Valor Medio por Transferencia</p>
              <p className="text-xl font-bold text-amber-600">
                {formatCurrency(metrics.average_ticket)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
