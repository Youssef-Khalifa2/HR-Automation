import { useState } from 'react';
import { useSubmissions, useDeleteSubmission, useResendApproval, useToggleMedicalCard, useFinalizeOffboarding, useCreateSubmission } from '../hooks/useSubmissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { formatDate, getStatusBadgeVariant, getExitInterviewStatusBadgeVariant } from '../lib/utils';
import { Trash2, Eye, Send, Plus, CheckCircle, Flag, RefreshCw } from 'lucide-react';
import type { Submission, SubmissionCreate } from '../lib/types';
import toast from 'react-hot-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';

export default function SubmissionsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [viewSubmission, setViewSubmission] = useState<Submission | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newSubmission, setNewSubmission] = useState<SubmissionCreate>({
    employee_name: '',
    employee_email: '',
    joining_date: '',
    submission_date: new Date().toISOString().split('T')[0],
    last_working_day: '',
  });

  const { data: submissions, isLoading, refetch } = useSubmissions({
    resignation_status: statusFilter && statusFilter !== 'all' ? statusFilter : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  });

  const deleteSubmission = useDeleteSubmission();
  const resendApproval = useResendApproval();
  const toggleMedicalCard = useToggleMedicalCard();
  const finalizeOffboarding = useFinalizeOffboarding();
  const createSubmission = useCreateSubmission();

  const handleRefresh = async () => {
    toast.promise(
      refetch(),
      {
        loading: 'Refreshing submissions...',
        success: 'Submissions refreshed successfully',
        error: 'Failed to refresh submissions'
      }
    );
  };

  const handleCreateSubmission = () => {
    // Validate required fields
    if (!newSubmission.employee_name || !newSubmission.employee_email ||
        !newSubmission.joining_date || !newSubmission.last_working_day) {
      toast.error('Please fill in all required fields');
      return;
    }

    createSubmission.mutate(newSubmission, {
      onSuccess: () => {
        setCreateModalOpen(false);
        setNewSubmission({
          employee_name: '',
          employee_email: '',
          joining_date: '',
          submission_date: new Date().toISOString().split('T')[0],
          last_working_day: '',
        });
      }
    });
  };

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

  const handleToggleMedicalCard = (id: number) => {
    if (confirm('Mark medical card as collected?')) {
      toggleMedicalCard.mutate(id, {
        onSuccess: () => setViewSubmission(null)
      });
    }
  };

  const handleFinalize = (id: number) => {
    const finalNotes = prompt('Enter any final notes (optional):');
    if (finalNotes !== null) { // null means cancelled
      finalizeOffboarding.mutate({ id, finalNotes }, {
        onSuccess: () => setViewSubmission(null)
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Submissions</h1>
          <p className="text-muted-foreground">Manage employee resignation submissions</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Submission
          </Button>
        </div>
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

            {/* Action Buttons */}
            <div className="border-t pt-4 mt-4 space-y-2">
              <h3 className="font-semibold text-sm mb-2">Actions</h3>
              <div className="flex gap-2 flex-wrap">
                {/* Medical Card Toggle - Show if IT assets cleared but medical card not collected */}
                {viewSubmission.it_support_reply && !viewSubmission.medical_card_collected && (
                  <Button
                    size="sm"
                    variant="default"
                    onClick={() => handleToggleMedicalCard(viewSubmission.id)}
                    disabled={toggleMedicalCard.isPending}
                  >
                    <CheckCircle className="mr-2 h-4 w-4" />
                    {toggleMedicalCard.isPending ? 'Marking...' : 'Mark Medical Card Collected'}
                  </Button>
                )}

                {/* Finalize Button - Show if medical card collected and not yet offboarded */}
                {viewSubmission.medical_card_collected &&
                 viewSubmission.it_support_reply &&
                 viewSubmission.resignation_status === 'medical_checked' && (
                  <Button
                    size="sm"
                    variant="default"
                    className="bg-green-600 hover:bg-green-700"
                    onClick={() => handleFinalize(viewSubmission.id)}
                    disabled={finalizeOffboarding.isPending}
                  >
                    <Flag className="mr-2 h-4 w-4" />
                    {finalizeOffboarding.isPending ? 'Finalizing...' : 'Finalize Offboarding'}
                  </Button>
                )}

                {/* Status indicator for finalized */}
                {viewSubmission.vendor_mail_sent && (
                  <div className="flex items-center text-sm text-green-600">
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Offboarding Complete - Vendor Notified
                  </div>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Create Submission Dialog */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New Resignation Submission</DialogTitle>
            <DialogDescription>
              Create a new employee resignation submission to start the offboarding process
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="employee_name">Employee Name *</Label>
              <Input
                id="employee_name"
                placeholder="e.g. John Doe"
                value={newSubmission.employee_name}
                onChange={(e) => setNewSubmission({ ...newSubmission, employee_name: e.target.value })}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="employee_email">Employee Email *</Label>
              <Input
                id="employee_email"
                type="email"
                placeholder="e.g. john.doe@company.com"
                value={newSubmission.employee_email}
                onChange={(e) => setNewSubmission({ ...newSubmission, employee_email: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="joining_date">Joining Date *</Label>
                <Input
                  id="joining_date"
                  type="date"
                  value={newSubmission.joining_date}
                  onChange={(e) => setNewSubmission({ ...newSubmission, joining_date: e.target.value })}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="submission_date">Submission Date *</Label>
                <Input
                  id="submission_date"
                  type="date"
                  value={newSubmission.submission_date}
                  onChange={(e) => setNewSubmission({ ...newSubmission, submission_date: e.target.value })}
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="last_working_day">Last Working Day *</Label>
              <Input
                id="last_working_day"
                type="date"
                value={newSubmission.last_working_day}
                onChange={(e) => setNewSubmission({ ...newSubmission, last_working_day: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">
                The notice period will be calculated automatically based on joining date
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateSubmission} disabled={createSubmission.isPending}>
              {createSubmission.isPending ? 'Creating...' : 'Create Submission'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
