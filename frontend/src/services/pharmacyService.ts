import api from './api';
import type { PharmacyDistribution, PartnerPharmacyDistribution } from '../types';

export const pharmacyService = {
  async getActiveCount(): Promise<{ active_pharmacies: number }> {
    const response = await api.get<{ active_pharmacies: number }>(
      '/pharmacies/count/active'
    );
    return response.data;
  },

  async getDistributionByProvince(): Promise<PharmacyDistribution[]> {
    const response = await api.get<PharmacyDistribution[]>(
      '/pharmacies/distribution/province'
    );
    return response.data;
  },

  async getDistributionByCity(): Promise<PharmacyDistribution[]> {
    const response = await api.get<PharmacyDistribution[]>(
      '/pharmacies/distribution/city'
    );
    return response.data;
  },

  async getPartnerDistribution(): Promise<PartnerPharmacyDistribution[]> {
    const response = await api.get<PartnerPharmacyDistribution[]>(
      '/pharmacies/distribution/partner'
    );
    return response.data;
  },
};


