import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type { ExitInterview, ExitInterviewSchedule, ExitInterviewFeedback, ExitInterviewStats } from '../lib/types';
import toast from 'react-hot-toast';

export const useUpcomingInterviews = (daysAhead: number = 30) => {
  return useQuery({
    queryKey: ['upcomingInterviews', daysAhead],
    queryFn: async () => {
      const { data } = await api.get<{interviews: any[]}>('/api/submissions/exit-interviews/upcoming', {
        params: { days_ahead: daysAhead },
      });
      return data.interviews || [];
    },
  });
};

export const usePendingFeedback = () => {
  return useQuery({
    queryKey: ['pendingFeedback'],
    queryFn: async () => {
      const { data } = await api.get<{interviews: any[]}>('/api/submissions/exit-interviews/pending-feedback');
      return data.interviews || [];
    },
  });
};

export const usePendingScheduling = () => {
  return useQuery({
    queryKey: ['pendingScheduling'],
    queryFn: async () => {
      const { data } = await api.get<{pending_interviews: any[]}>('/api/submissions/exit-interviews/pending-scheduling');
      return data.pending_interviews || [];
    },
  });
};

export const useExitInterviewStats = () => {
  return useQuery({
    queryKey: ['exitInterviewStats'],
    queryFn: async () => {
      const { data } = await api.get<{statistics: ExitInterviewStats}>('/api/submissions/exit-interviews/statistics');
      return data.statistics;
    },
  });
};

export const useScheduleInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scheduleData: ExitInterviewSchedule) => {
      const { data } = await api.post('/api/submissions/exit-interviews/schedule/', scheduleData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['upcomingInterviews'] });
      queryClient.invalidateQueries({ queryKey: ['pendingScheduling'] });
      queryClient.invalidateQueries({ queryKey: ['exitInterviewStats'] });
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      toast.success('Interview scheduled successfully');
    },
    onError: () => {
      toast.error('Failed to schedule interview');
    },
  });
};

export const useSubmitFeedback = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (feedbackData: ExitInterviewFeedback) => {
      const { data } = await api.post('/api/submissions/exit-interviews/submit-feedback/', feedbackData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['upcomingInterviews'] });
      queryClient.invalidateQueries({ queryKey: ['pendingFeedback'] });
      queryClient.invalidateQueries({ queryKey: ['exitInterviewStats'] });
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      toast.success('Feedback submitted successfully');
    },
    onError: () => {
      toast.error('Failed to submit feedback');
    },
  });
};

export const useSkipInterview = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { submission_id: number; reason?: string }) => {
      const response = await api.post('/api/forms/skip-interview-dashboard', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
      queryClient.invalidateQueries({ queryKey: ['pendingScheduling'] });
      queryClient.invalidateQueries({ queryKey: ['exitInterviewStats'] });
      toast.success('Interview skipped successfully');
    },
    onError: () => {
      toast.error('Failed to skip interview');
    },
  });
};

export const useAllExitInterviews = () => {
  return useQuery({
    queryKey: ['allExitInterviews'],
    queryFn: async () => {
      const { data } = await api.get<any[]>('/api/submissions/exit-interviews/list');
      return data || [];
    },
  });
};
