import { useState } from 'react';
import FilterBar from '../components/FilterBar';
import MetricCard from '../components/MetricCard';
import { useShortageMetrics } from '../hooks/useShortage';
import type { PeriodType } from '../types';

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

  const { data, loading, error } = useShortageMetrics(
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
      <div className="flex items-start justify-between animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Shortage Metrics
          </h1>
          <p className="text-gray-500">
            Métricas de transferencias internas entre farmacias
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

      {/* Filter Bar */}
      <div className="card p-4 animate-fade-in stagger-1 relative" style={{ zIndex: 100 }}>
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

          {/* Summary Card */}
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
        </>
      )}
    </div>
  );
}
