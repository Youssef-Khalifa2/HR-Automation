import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { LeaderMapping, LeaderInfo } from '../lib/types';
import toast from 'react-hot-toast';

// Fetch all leaders
export function useLeaders() {
  return useQuery({
    queryKey: ['leaders'],
    queryFn: async () => {
      const response = await api.get<{ leaders: LeaderMapping }>('/api/mapping/leaders');
      return response.data.leaders;
    },
  });
}

// Fetch all CHMs (Chinese Heads)
export function useCHMs() {
  return useQuery({
    queryKey: ['chms'],
    queryFn: async () => {
      const response = await api.get<{ chms: LeaderMapping }>('/api/mapping/chms');
      return response.data.chms || {};
    },
  });
}

// Reload mappings from CSV
export function useReloadMappings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/api/mapping/reload');
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate all mapping-related queries to force refetch
      queryClient.invalidateQueries({ queryKey: ['leaders'] });
      queryClient.invalidateQueries({ queryKey: ['chms'] });
      queryClient.invalidateQueries({ queryKey: ['mapping-health'] });
      toast.success(`Mappings reloaded: ${data.leaders_count} leaders found`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to reload mappings');
    },
  });
}

// Fetch leader info by name (includes CHM details)
export function useLeaderInfo(leaderName: string | null) {
  return useQuery({
    queryKey: ['leader-info', leaderName],
    queryFn: async () => {
      if (!leaderName) return null;
      const response = await api.get<LeaderInfo>(`/api/mapping/leader/${leaderName}`);
      return response.data;
    },
    enabled: !!leaderName,
  });
}

// Mapping health check
export function useMappingHealth() {
  return useQuery({
    queryKey: ['mapping-health'],
    queryFn: async () => {
      const response = await api.get('/api/mapping/health');
      return response.data;
    },
  });
}
