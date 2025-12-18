import { useState, useEffect, useCallback } from 'react';
import { shortageService } from '../services/shortageService';
import type { PeriodType, ShortageResponse, ShortageTimeSeriesResponse } from '../types';

export type ChartGroupBy = 'week' | 'month' | 'quarter' | 'year';

export function useShortageMetrics(
  periodType: PeriodType = 'this_month',
  startDate?: string,
  endDate?: string
) {
  const [data, setData] = useState<ShortageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await shortageService.getMetrics(
        periodType,
        startDate,
        endDate
      );
      setData(result);
    } catch (err) {
      setError('Error loading shortage metrics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [periodType, startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useShortageTimeSeries(
  periodType: PeriodType = 'this_year',
  groupBy: ChartGroupBy = 'month',
  startDate?: string,
  endDate?: string
) {
  const [data, setData] = useState<ShortageTimeSeriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await shortageService.getTimeSeries(
        periodType,
        groupBy,
        startDate,
        endDate
      );
      setData(result);
    } catch (err) {
      setError('Error loading shortage time series');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [periodType, groupBy, startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}


