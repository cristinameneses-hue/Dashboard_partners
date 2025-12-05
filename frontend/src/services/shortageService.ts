import api from './api';
import type { PeriodType, ShortageResponse } from '../types';

export const shortageService = {
  async getMetrics(
    periodType: PeriodType = 'this_month',
    startDate?: string,
    endDate?: string
  ): Promise<ShortageResponse> {
    const params = new URLSearchParams();
    params.append('period_type', periodType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await api.get<ShortageResponse>(`/shortage?${params}`);
    return response.data;
  },
};


