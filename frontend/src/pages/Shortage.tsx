import { useState } from 'react';
import FilterBar from '../components/FilterBar';
import MetricCard from '../components/MetricCard';
import { useShortageMetrics } from '../hooks/useShortage';
import type { PeriodType } from '../types';

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

  const metrics = data?.metrics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Shortage Metrics
          </h1>
          <p className="text-slate-400">
            Métricas de transferencias internas entre farmacias
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
            <h2 className="text-lg font-semibold text-white mb-4">Bookings</h2>
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
                title="% Cancelled"
                value={`${metrics.pct_cancelled_bookings.toFixed(1)}%`}
                color="red"
              />
              <MetricCard
                title="Avg Orders/Pharm"
                value={metrics.avg_orders_per_pharmacy.toFixed(1)}
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
            <h2 className="text-lg font-semibold text-white mb-4">GMV</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <MetricCard
                title="Gross GMV"
                value={formatCurrency(metrics.gross_gmv)}
                color="amber"
              />
              <MetricCard
                title="Cancelled GMV"
                value={formatCurrency(metrics.cancelled_gmv)}
                color="red"
              />
              <MetricCard
                title="Net GMV"
                value={formatCurrency(metrics.net_gmv)}
                color="green"
                size="lg"
              />
              <MetricCard
                title="% Cancelled GMV"
                value={`${metrics.pct_cancelled_gmv.toFixed(1)}%`}
                color="red"
              />
              <MetricCard
                title="Avg GMV/Pharm"
                value={formatCurrency(metrics.avg_gmv_per_pharmacy)}
                color="cyan"
              />
            </div>
          </div>

          {/* Pharmacy Metrics */}
          <div className="animate-fade-in stagger-4">
            <h2 className="text-lg font-semibold text-white mb-4">Farmacias</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card p-6 bg-gradient-to-br from-emerald-500/20 to-emerald-600/5 border border-emerald-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                      Farmacias Activas
                    </p>
                    <p className="text-3xl font-bold text-emerald-400">
                      {formatNumber(metrics.active_pharmacies)}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Total con active=1</p>
                  </div>
                  <div className="text-4xl text-emerald-400/50">◉</div>
                </div>
              </div>

              <div className="card p-6 bg-gradient-to-br from-amber-500/20 to-amber-600/5 border border-amber-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                      Farmacias Emisoras
                    </p>
                    <p className="text-3xl font-bold text-amber-400">
                      {formatNumber(metrics.sending_pharmacies)}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Mín. 1 shortage enviado</p>
                  </div>
                  <div className="text-4xl text-amber-400/50">↑</div>
                </div>
              </div>

              <div className="card p-6 bg-gradient-to-br from-sky-500/20 to-sky-600/5 border border-sky-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                      Farmacias Receptoras
                    </p>
                    <p className="text-3xl font-bold text-sky-400">
                      {formatNumber(metrics.receiving_pharmacies)}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">Mín. 1 shortage recibido</p>
                  </div>
                  <div className="text-4xl text-sky-400/50">↓</div>
                </div>
              </div>
            </div>
          </div>

          {/* Summary Card */}
          <div className="card p-6 animate-fade-in">
            <h3 className="font-semibold text-white mb-4">Resumen</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-slate-400">Total Transferencias</p>
                <p className="text-xl font-bold text-white">
                  {formatNumber(metrics.net_bookings)}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Valor Total</p>
                <p className="text-xl font-bold text-emerald-400">
                  {formatCurrency(metrics.net_gmv)}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Tasa de Cancelación</p>
                <p className={`text-xl font-bold ${metrics.pct_cancelled_bookings > 10 ? 'text-red-400' : 'text-white'}`}>
                  {metrics.pct_cancelled_bookings.toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Valor Medio por Transferencia</p>
                <p className="text-xl font-bold text-amber-400">
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
