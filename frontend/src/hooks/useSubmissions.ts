import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { Submission, SubmissionCreate, SubmissionUpdate, SubmissionFilters } from '../lib/types';
import toast from 'react-hot-toast';

export const useSubmissions = (filters?: SubmissionFilters) => {
  return useQuery({
    queryKey: ['submissions', filters],
    queryFn: async () => {
      const { data } = await api.get<Submission[]>('/api/submissions/', { params: filters });
      return data;
    },
  });
};

export const useSubmission = (id: number) => {
  return useQuery({
    queryKey: ['submission', id],
    queryFn: async () => {
      const { data } = await api.get<Submission>(`/api/submissions/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateSubmission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (submission: SubmissionCreate) => {
      const { data } = await api.post<Submission>('/api/submissions/', submission);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      toast.success('Submission created successfully');
    },
    onError: () => {
      toast.error('Failed to create submission');
    },
  });
};

export const useUpdateSubmission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: SubmissionUpdate }) => {
      const response = await api.patch<Submission>(`/api/submissions/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['submission'] });
      toast.success('Submission updated successfully');
    },
    onError: () => {
      toast.error('Failed to update submission');
    },
  });
};

export const useDeleteSubmission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/submissions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      toast.success('Submission deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete submission');
    },
  });
};

export const useResendApproval = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post(`/api/submissions/${id}/resend`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      toast.success('Approval request resent successfully');
    },
    onError: () => {
      toast.error('Failed to resend approval request');
    },
  });
};
