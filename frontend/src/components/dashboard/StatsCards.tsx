import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { FileText, Clock, CheckCircle, Users } from 'lucide-react';
import type { DashboardStats } from '../../lib/types';

interface StatsCardsProps {
  stats: DashboardStats;
  isLoading: boolean;
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">-</div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Submissions',
      value: stats.total_submissions,
      icon: FileText,
      color: 'text-blue-600',
    },
    {
      title: 'Pending Approvals',
      value: stats.pending_approvals,
      icon: Clock,
      color: 'text-orange-600',
    },
    {
      title: 'Completed This Month',
      value: stats.completed_this_month,
      icon: CheckCircle,
      color: 'text-green-600',
    },
    {
      title: 'Exit Interviews',
      value: stats.exit_interviews,
      icon: Users,
      color: 'text-purple-600',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
