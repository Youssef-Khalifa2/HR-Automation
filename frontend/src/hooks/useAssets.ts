import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import toast from 'react-hot-toast';
import type { Asset, AssetCreate, AssetUpdate } from '../lib/types';

// Fetch all assets with optional filters
export const useAssets = (filters?: {
  returned?: boolean;
  submission_id?: number;
}) => {
  return useQuery({
    queryKey: ['assets', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.returned !== undefined) params.append('returned', filters.returned.toString());
      if (filters?.submission_id) params.append('submission_id', filters.submission_id.toString());

      const queryString = params.toString();
      const url = queryString ? `/api/assets/?${queryString}` : '/api/assets/';
      const { data } = await api.get<Asset[]>(url);
      return data;
    },
  });
};

// Fetch single asset by ID
export const useAsset = (id: number) => {
  return useQuery({
    queryKey: ['asset', id],
    queryFn: async () => {
      const { data } = await api.get<Asset>(`/api/assets/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

// Create or update asset for a submission
export const useCreateOrUpdateAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ submission_id, asset }: { submission_id: number; asset: AssetCreate }) => {
      const { data } = await api.post<Asset>(`/api/assets/submissions/${submission_id}/assets`, asset);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      toast.success('Asset record updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update asset');
    },
  });
};

// Mark asset as returned
export const useMarkAssetReturned = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (asset_id: number) => {
      const { data } = await api.post(`/api/assets/${asset_id}/mark-returned`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      toast.success('Assets marked as returned');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to mark assets as returned');
    },
  });
};

// Get asset statistics
export const useAssetStats = () => {
  return useQuery({
    queryKey: ['asset-stats'],
    queryFn: async () => {
      const { data } = await api.get('/api/assets/stats');
      return data;
    },
  });
};
