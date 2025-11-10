import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import type { Submission, DashboardStats } from '../lib/types';

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      // Calculate stats from submissions
      const { data: submissions } = await api.get<Submission[]>('/api/submissions/');

      const stats: DashboardStats = {
        total_submissions: submissions.length,
        pending_approvals: submissions.filter(
          (s) => s.resignation_status === 'submitted' || s.resignation_status === 'leader_approved'
        ).length,
        completed_this_month: submissions.filter((s) => {
          const createdDate = new Date(s.created_at);
          const now = new Date();
          return (
            createdDate.getMonth() === now.getMonth() &&
            createdDate.getFullYear() === now.getFullYear() &&
            s.resignation_status === 'offboarded'
          );
        }).length,
        exit_interviews: submissions.filter(
          (s) => s.exit_interview_status === 'scheduled' || s.exit_interview_status === 'done'
        ).length,
      };

      return stats;
    },
  });
};

export const useRecentSubmissions = (limit: number = 10) => {
  return useQuery({
    queryKey: ['recentSubmissions', limit],
    queryFn: async () => {
      const { data } = await api.get<Submission[]>('/api/submissions/', {
        params: { limit },
      });
      return data;
    },
  });
};
