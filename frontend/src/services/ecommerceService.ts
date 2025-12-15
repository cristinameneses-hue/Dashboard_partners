import api from './api';
import type {
  PeriodType,
  EcommerceResponse,
  EcommerceMetrics,
  PartnerInfo,
  TimeSeriesResponse,
} from '../types';

export const ecommerceService = {
  async getMetrics(
    periodType: PeriodType = 'this_month',
    startDate?: string,
    endDate?: string
  ): Promise<EcommerceResponse> {
    const params = new URLSearchParams();
    params.append('period_type', periodType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get<EcommerceResponse>(`/ecommerce?${params}`);
    return response.data;
  },

  async getPartnerMetrics(
    partner: string,
    periodType: PeriodType = 'this_month',
    startDate?: string,
    endDate?: string
  ): Promise<EcommerceMetrics> {
    const params = new URLSearchParams();
    params.append('period_type', periodType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get<EcommerceMetrics>(
      `/ecommerce/partner/${partner}?${params}`
    );
    return response.data;
  },

  async getPartners(): Promise<PartnerInfo[]> {
    const response = await api.get<PartnerInfo[]>('/ecommerce/partners');
    return response.data;
  },

  async getTimeSeries(
    periodType: PeriodType = 'this_year',
    groupBy: string = 'month',
    partners?: string[],
    startDate?: string,
    endDate?: string
  ): Promise<TimeSeriesResponse> {
    const params = new URLSearchParams();
    params.append('period_type', periodType);
    params.append('group_by', groupBy);
    if (partners && partners.length > 0) {
      params.append('partners', partners.join(','));
    }
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get<TimeSeriesResponse>(`/ecommerce/timeseries?${params}`);
    return response.data;
  },
};


