import { StatsCards } from '../components/dashboard/StatsCards';
import { useDashboardStats, useRecentSubmissions } from '../hooks/useDashboard';
import { useUpcomingInterviews, usePendingFeedback } from '../hooks/useExitInterviews';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { formatDate, getStatusBadgeVariant, getExitInterviewStatusBadgeVariant } from '../lib/utils';
import { Calendar, Clock } from 'lucide-react';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: recentSubmissions, isLoading: submissionsLoading } = useRecentSubmissions(10);
  const { data: upcomingInterviews, isLoading: interviewsLoading } = useUpcomingInterviews(7);
  const { data: pendingFeedback, isLoading: feedbackLoading } = usePendingFeedback();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Overview of employee offboarding activities</p>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats || { total_submissions: 0, pending_approvals: 0, completed_this_month: 0, exit_interviews: 0 }} isLoading={statsLoading} />

      <div className="grid gap-6 md:grid-cols-2">
        {/* Upcoming Interviews */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Upcoming Interviews (7 days)
            </CardTitle>
            <CardDescription>Exit interviews scheduled in the next week</CardDescription>
          </CardHeader>
          <CardContent>
            {interviewsLoading ? (
              <div className="text-center text-muted-foreground">Loading...</div>
            ) : upcomingInterviews && upcomingInterviews.length > 0 ? (
              <div className="space-y-3">
                {upcomingInterviews.map((interview) => (
                  <div key={interview.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                    <div>
                      <p className="font-medium">{interview.submission?.employee_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(interview.scheduled_date)} at {interview.scheduled_time}
                      </p>
                      <p className="text-xs text-muted-foreground">{interview.location}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-muted-foreground">No upcoming interviews</div>
            )}
          </CardContent>
        </Card>

        {/* Pending Feedback */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Pending Feedback
            </CardTitle>
            <CardDescription>Interviews awaiting feedback submission</CardDescription>
          </CardHeader>
          <CardContent>
            {feedbackLoading ? (
              <div className="text-center text-muted-foreground">Loading...</div>
            ) : pendingFeedback && pendingFeedback.length > 0 ? (
              <div className="space-y-3">
                {pendingFeedback.map((interview) => (
                  <div key={interview.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                    <div>
                      <p className="font-medium">{interview.submission?.employee_name}</p>
                      <p className="text-sm text-muted-foreground">
                        Interviewed on {formatDate(interview.scheduled_date)}
                      </p>
                    </div>
                    <Badge variant="destructive">Overdue</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-muted-foreground">No pending feedback</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Submissions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Submissions</CardTitle>
          <CardDescription>Latest resignation submissions</CardDescription>
        </CardHeader>
        <CardContent>
          {submissionsLoading ? (
            <div className="text-center text-muted-foreground">Loading...</div>
          ) : recentSubmissions && recentSubmissions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Exit Interview</TableHead>
                  <TableHead>Last Working Day</TableHead>
                  <TableHead>Submitted</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentSubmissions.map((submission) => (
                  <TableRow key={submission.id}>
                    <TableCell className="font-medium">{submission.employee_name}</TableCell>
                    <TableCell>{submission.employee_email}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(submission.resignation_status)}>
                        {submission.resignation_status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getExitInterviewStatusBadgeVariant(submission.exit_interview_status)}>
                        {submission.exit_interview_status}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(submission.last_working_day)}</TableCell>
                    <TableCell>{formatDate(submission.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center text-muted-foreground">No submissions found</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
