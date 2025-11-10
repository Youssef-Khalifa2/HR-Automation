import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import toast from 'react-hot-toast';
import type { Asset, AssetCreate, AssetUpdate } from '../lib/types';

// Fetch all assets with optional filters
export const useAssets = (filters?: {
  pending?: boolean;
  approved?: boolean;
  submission_id?: number;
}) => {
  return useQuery({
    queryKey: ['assets', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.pending !== undefined) params.append('pending', filters.pending.toString());
      if (filters?.approved !== undefined) params.append('approved', filters.approved.toString());
      if (filters?.submission_id) params.append('submission_id', filters.submission_id.toString());

      const { data } = await api.get<Asset[]>(`/api/assets?${params.toString()}`);
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

// Approve asset clearance
export const useApproveAsset = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (asset_id: number) => {
      const { data } = await api.post(`/api/assets/${asset_id}/approve`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      toast.success('Asset clearance approved');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve asset');
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

// Get pending asset approvals
export const usePendingAssetApprovals = () => {
  return useQuery({
    queryKey: ['pending-asset-approvals'],
    queryFn: async () => {
      const { data } = await api.get<Asset[]>('/api/assets?pending=true');
      return data;
    },
  });
};
