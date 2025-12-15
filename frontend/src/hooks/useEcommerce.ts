import { useState, useEffect, useCallback } from 'react';
import { ecommerceService } from '../services/ecommerceService';
import type { PeriodType, EcommerceResponse, PartnerInfo, TimeSeriesResponse } from '../types';

export function useEcommerceMetrics(
  periodType: PeriodType = 'this_month',
  startDate?: string,
  endDate?: string
) {
  const [data, setData] = useState<EcommerceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await ecommerceService.getMetrics(
        periodType,
        startDate,
        endDate
      );
      setData(result);
    } catch (err) {
      setError('Error loading ecommerce metrics');
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

export function usePartners() {
  const [partners, setPartners] = useState<PartnerInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPartners() {
      try {
        const result = await ecommerceService.getPartners();
        setPartners(result);
      } catch (err) {
        console.error('Error loading partners:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchPartners();
  }, []);

  return { partners, loading };
}

export type ChartGroupBy = 'week' | 'month' | 'quarter' | 'year';

export function useTimeSeries(
  periodType: PeriodType = 'this_year',
  groupBy: ChartGroupBy = 'month',
  partners?: string[],
  startDate?: string,
  endDate?: string
) {
  const [data, setData] = useState<TimeSeriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await ecommerceService.getTimeSeries(
        periodType,
        groupBy,
        partners,
        startDate,
        endDate
      );
      setData(result);
    } catch (err) {
      setError('Error loading time series data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [periodType, groupBy, partners?.join(','), startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}


