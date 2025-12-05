import { useState } from 'react';
import type { PeriodType } from '../types';
import { PERIOD_OPTIONS } from '../types';

interface PeriodSelectorProps {
  value: PeriodType;
  onChange: (period: PeriodType, startDate?: string, endDate?: string) => void;
  startDate?: string;
  endDate?: string;
}

export default function PeriodSelector({
  value,
  onChange,
  startDate,
  endDate,
}: PeriodSelectorProps) {
  const [customStart, setCustomStart] = useState(startDate || '');
  const [customEnd, setCustomEnd] = useState(endDate || '');

  const handlePeriodChange = (newPeriod: PeriodType) => {
    if (newPeriod === 'custom') {
      onChange(newPeriod, customStart, customEnd);
    } else {
      onChange(newPeriod);
    }
  };

  const handleCustomDateChange = () => {
    if (customStart && customEnd) {
      onChange('custom', customStart, customEnd);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Period Type Buttons */}
      <div className="flex flex-wrap gap-2">
        {PERIOD_OPTIONS.map((option) => (
          <button
            key={option.value}
            onClick={() => handlePeriodChange(option.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              value === option.value
                ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/25'
                : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600 hover:text-white'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Custom Date Inputs */}
      {value === 'custom' && (
        <div className="flex items-center gap-2 animate-fade-in">
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="input text-sm py-1.5"
          />
          <span className="text-slate-400">to</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="input text-sm py-1.5"
          />
          <button
            onClick={handleCustomDateChange}
            className="btn btn-primary text-sm py-1.5"
            disabled={!customStart || !customEnd}
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
}
