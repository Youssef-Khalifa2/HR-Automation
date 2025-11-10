import { useState } from 'react';
import { useSubmissions, useDeleteSubmission, useResendApproval } from '../hooks/useSubmissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { formatDate, getStatusBadgeVariant, getExitInterviewStatusBadgeVariant } from '../lib/utils';
import { Trash2, Eye, Send, Plus } from 'lucide-react';
import type { Submission } from '../lib/types';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

export default function SubmissionsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [viewSubmission, setViewSubmission] = useState<Submission | null>(null);

  const { data: submissions, isLoading } = useSubmissions({
    resignation_status: statusFilter && statusFilter !== 'all' ? statusFilter : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const deleteSubmission = useDeleteSubmission();
  const resendApproval = useResendApproval();

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this submission?')) {
      deleteSubmission.mutate(id);
    }
  };

  const handleResend = (id: number) => {
    if (confirm('Resend approval request emails?')) {
      resendApproval.mutate(id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Submissions</h1>
          <p className="text-muted-foreground">Manage employee resignation submissions</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Submission
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <label className="text-sm font-medium">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="submitted">Submitted</SelectItem>
                  <SelectItem value="leader_approved">Leader Approved</SelectItem>
                  <SelectItem value="leader_rejected">Leader Rejected</SelectItem>
                  <SelectItem value="chm_approved">CHM Approved</SelectItem>
                  <SelectItem value="chm_rejected">CHM Rejected</SelectItem>
                  <SelectItem value="exit_done">Exit Done</SelectItem>
                  <SelectItem value="offboarded">Offboarded</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">From Date</label>
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">To Date</label>
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setStatusFilter('');
                  setDateFrom('');
                  setDateTo('');
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Submissions Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Submissions</CardTitle>
          <CardDescription>
            {submissions ? `${submissions.length} submission(s) found` : 'Loading...'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center text-muted-foreground">Loading...</div>
          ) : submissions && submissions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Exit Interview</TableHead>
                  <TableHead>Last Working Day</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {submissions.map((submission) => (
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
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setViewSubmission(submission)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleResend(submission.id)}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDelete(submission.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center text-muted-foreground">No submissions found</div>
          )}
        </CardContent>
      </Card>

      {/* View Submission Dialog */}
      {viewSubmission && (
        <Dialog open={!!viewSubmission} onOpenChange={() => setViewSubmission(null)}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Submission Details</DialogTitle>
              <DialogDescription>
                Viewing details for {viewSubmission.employee_name}
              </DialogDescription>
            </DialogHeader>
            <Tabs defaultValue="employee">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="employee">Employee Info</TabsTrigger>
                <TabsTrigger value="workflow">Workflow</TabsTrigger>
                <TabsTrigger value="additional">Additional</TabsTrigger>
              </TabsList>
              <TabsContent value="employee" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium">Name</p>
                    <p className="text-sm text-muted-foreground">{viewSubmission.employee_name}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Email</p>
                    <p className="text-sm text-muted-foreground">{viewSubmission.employee_email}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Joining Date</p>
                    <p className="text-sm text-muted-foreground">{formatDate(viewSubmission.joining_date)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Submission Date</p>
                    <p className="text-sm text-muted-foreground">{formatDate(viewSubmission.submission_date)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Last Working Day</p>
                    <p className="text-sm text-muted-foreground">{formatDate(viewSubmission.last_working_day)}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Notice Period</p>
                    <p className="text-sm text-muted-foreground">{viewSubmission.notice_period_days} days</p>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="workflow" className="space-y-4">
                <div>
                  <p className="text-sm font-medium">Resignation Status</p>
                  <Badge variant={getStatusBadgeVariant(viewSubmission.resignation_status)}>
                    {viewSubmission.resignation_status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium">Exit Interview Status</p>
                  <Badge variant={getExitInterviewStatusBadgeVariant(viewSubmission.exit_interview_status)}>
                    {viewSubmission.exit_interview_status}
                  </Badge>
                </div>
                {viewSubmission.team_leader_reply !== null && (
                  <div>
                    <p className="text-sm font-medium">Team Leader Reply</p>
                    <p className="text-sm text-muted-foreground">
                      {viewSubmission.team_leader_reply ? 'Approved' : 'Rejected'}
                    </p>
                    {viewSubmission.team_leader_notes && (
                      <p className="text-sm text-muted-foreground mt-1">{viewSubmission.team_leader_notes}</p>
                    )}
                  </div>
                )}
                {viewSubmission.chinese_head_reply !== null && (
                  <div>
                    <p className="text-sm font-medium">CHM Reply</p>
                    <p className="text-sm text-muted-foreground">
                      {viewSubmission.chinese_head_reply ? 'Approved' : 'Rejected'}
                    </p>
                    {viewSubmission.chinese_head_notes && (
                      <p className="text-sm text-muted-foreground mt-1">{viewSubmission.chinese_head_notes}</p>
                    )}
                  </div>
                )}
              </TabsContent>
              <TabsContent value="additional" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium">In Probation</p>
                    <p className="text-sm text-muted-foreground">{viewSubmission.in_probation ? 'Yes' : 'No'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Medical Card Collected</p>
                    <p className="text-sm text-muted-foreground">{viewSubmission.medical_card_collected ? 'Yes' : 'No'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Vendor Mail Sent</p>
                    <p className="text-sm text-muted-foreground">{viewSubmission.vendor_mail_sent ? 'Yes' : 'No'}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Created At</p>
                    <p className="text-sm text-muted-foreground">{formatDate(viewSubmission.created_at)}</p>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
