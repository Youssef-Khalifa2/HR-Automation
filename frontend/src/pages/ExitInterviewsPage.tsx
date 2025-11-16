import { useState } from 'react';
import {
  useUpcomingInterviews,
  usePendingFeedback,
  usePendingScheduling,
  useScheduleInterview,
  useSubmitFeedback,
  useSkipInterview,
  useExitInterviewStats,
  useAllExitInterviews,
} from '../hooks/useExitInterviews';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { formatDate } from '../lib/utils';
import { Calendar, CheckCircle, Clock, Users, RefreshCw, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import * as XLSX from 'xlsx';

export default function ExitInterviewsPage() {
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [skipModalOpen, setSkipModalOpen] = useState(false);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<number | null>(null);
  const [selectedInterviewId, setSelectedInterviewId] = useState<number | null>(null);

  const { data: stats, refetch: refetchStats } = useExitInterviewStats();
  const { data: upcoming, refetch: refetchUpcoming } = useUpcomingInterviews(30);
  const { data: pendingFeedback, refetch: refetchPendingFeedback } = usePendingFeedback();
  const { data: pendingScheduling, refetch: refetchPendingScheduling } = usePendingScheduling();
  const { data: allInterviews, refetch: refetchAllInterviews } = useAllExitInterviews();

  const handleRefresh = async () => {
    toast.promise(
      Promise.all([
        refetchStats(),
        refetchUpcoming(),
        refetchPendingFeedback(),
        refetchPendingScheduling(),
        refetchAllInterviews()
      ]),
      {
        loading: 'Refreshing interviews...',
        success: 'Interviews refreshed successfully',
        error: 'Failed to refresh interviews'
      }
    );
  };

  const exportToExcel = () => {
    if (!allInterviews || allInterviews.length === 0) {
      toast.error('No data to export');
      return;
    }

    // Prepare data for Excel
    const exportData = allInterviews.map((interview: any) => ({
      'Employee Name': interview.employee_name,
      'Department': interview.department,
      'Last Working Day': interview.last_working_day,
      'Interview Status': interview.status,
      'Interview Date/Time': interview.interview_datetime,
      'Location': interview.location || 'N/A',
      'Interviewer': interview.interviewer || 'N/A',
      'Reason to Leave': interview.reason_to_leave || '',
      'Feedback Notes': interview.feedback_notes || '',
      'HR Notes': interview.hr_notes || '',
    }));

    // Create workbook and worksheet
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(exportData);

    // Set column widths
    ws['!cols'] = [
      { wch: 20 }, // Employee Name
      { wch: 15 }, // Department
      { wch: 15 }, // Last Working Day
      { wch: 15 }, // Interview Status
      { wch: 20 }, // Interview Date/Time
      { wch: 20 }, // Location
      { wch: 20 }, // Interviewer
      { wch: 25 }, // Reason to Leave
      { wch: 40 }, // Feedback Notes
      { wch: 30 }, // HR Notes
    ];

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Exit Interviews');

    // Generate filename with current date
    const date = new Date().toISOString().split('T')[0];
    const filename = `Exit_Interviews_${date}.xlsx`;

    // Save file
    XLSX.writeFile(wb, filename);
    toast.success('Excel file exported successfully');
  };

  const scheduleInterview = useScheduleInterview();
  const submitFeedback = useSubmitFeedback();
  const skipInterview = useSkipInterview();

  const [scheduleForm, setScheduleForm] = useState({
    submission_id: 0,
    scheduled_date: '',
    scheduled_time: '',
    location: '',
    interviewer: '',
  });

  const [feedbackForm, setFeedbackForm] = useState({
    interview_id: 0,
    interview_feedback: '',
    reason_to_leave: '',
    hr_notes: '',
  });

  const handleSchedule = (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }

    // Validate all required fields
    if (!scheduleForm.submission_id || scheduleForm.submission_id === 0) {
      toast.error('Invalid submission ID');
      return;
    }

    if (!scheduleForm.scheduled_date) {
      toast.error('Please select an interview date');
      return;
    }

    if (!scheduleForm.scheduled_time) {
      toast.error('Please select an interview time');
      return;
    }

    if (!scheduleForm.location) {
      toast.error('Please enter the interview location');
      return;
    }

    if (!scheduleForm.interviewer) {
      toast.error('Please enter the interviewer name');
      return;
    }

    scheduleInterview.mutate(scheduleForm, {
      onSuccess: () => {
        setScheduleModalOpen(false);
        setScheduleForm({
          submission_id: 0,
          scheduled_date: '',
          scheduled_time: '',
          location: '',
          interviewer: '',
        });
      },
      onError: (error: any) => {
        console.error('Schedule interview error:', error);
        const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to schedule interview';
        toast.error(errorMessage);
      },
    });
  };

  const handleFeedbackSubmit = (e?: React.FormEvent) => {
    if (e) {
      e.preventDefault();
    }

    // Validate required fields
    if (!feedbackForm.interview_id || feedbackForm.interview_id === 0) {
      toast.error('Invalid interview ID');
      return;
    }

    if (!feedbackForm.interview_feedback || feedbackForm.interview_feedback.trim().length < 10) {
      toast.error('Please provide detailed feedback (at least 10 characters)');
      return;
    }

    if (!feedbackForm.reason_to_leave || feedbackForm.reason_to_leave.trim().length === 0) {
      toast.error('Please select a reason for leaving');
      return;
    }

    submitFeedback.mutate(feedbackForm, {
      onSuccess: () => {
        setFeedbackModalOpen(false);
        setFeedbackForm({
          interview_id: 0,
          interview_feedback: '',
          reason_to_leave: '',
          hr_notes: '',
        });
      },
      onError: (error: any) => {
        console.error('Submit feedback error:', error);
        const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to submit feedback';
        toast.error(errorMessage);
      },
    });
  };

  const handleSkip = () => {
    if (!selectedSubmissionId || selectedSubmissionId === 0) {
      toast.error('Invalid submission selected');
      return;
    }

    skipInterview.mutate({ submission_id: selectedSubmissionId }, {
      onSuccess: () => {
        setSkipModalOpen(false);
        setSelectedSubmissionId(null);
      },
      onError: (error: any) => {
        console.error('Skip interview error:', error);
        toast.error(error?.response?.data?.message || 'Failed to skip interview. Please try again.');
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Exit Interviews</h1>
          <p className="text-muted-foreground">Manage exit interview scheduling and feedback</p>
        </div>
        <Button onClick={handleRefresh} variant="outline" size="sm">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Interviews</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">To Schedule</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.to_schedule || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Upcoming</CardTitle>
            <Calendar className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.upcoming || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.completed || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Scheduling */}
      <Card>
        <CardHeader>
          <CardTitle>Pending Scheduling</CardTitle>
          <CardDescription>Employees awaiting interview scheduling</CardDescription>
        </CardHeader>
        <CardContent>
          {pendingScheduling && pendingScheduling.length > 0 ? (
            <div className="space-y-3">
              {pendingScheduling.map((submission: any) => (
                <div key={submission.submission_id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{submission.employee_name}</p>
                    <p className="text-sm text-muted-foreground">{submission.employee_email}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => {
                        setScheduleForm({ ...scheduleForm, submission_id: submission.submission_id });
                        setScheduleModalOpen(true);
                      }}
                    >
                      Schedule
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setSelectedSubmissionId(submission.submission_id);
                        setSkipModalOpen(true);
                      }}
                    >
                      Skip
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-muted-foreground">No pending scheduling</div>
          )}
        </CardContent>
      </Card>

      {/* Upcoming Interviews */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Interviews</CardTitle>
          <CardDescription>Scheduled interviews in the next 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          {upcoming && upcoming.length > 0 ? (
            <div className="space-y-3">
              {upcoming.map((interview) => (
                <div key={interview.interview_id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{interview.employee_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(interview.scheduled_date)} at {interview.scheduled_time}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {interview.location} | {interview.interviewer}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setSelectedSubmissionId(interview.submission_id);
                      setSkipModalOpen(true);
                    }}
                  >
                    Skip
                  </Button>
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
          <CardTitle>Pending Feedback</CardTitle>
          <CardDescription>Completed interviews awaiting feedback</CardDescription>
        </CardHeader>
        <CardContent>
          {pendingFeedback && pendingFeedback.length > 0 ? (
            <div className="space-y-3">
              {pendingFeedback.map((interview) => (
                <div key={interview.interview_id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{interview.employee_name}</p>
                    <p className="text-sm text-muted-foreground">
                      Interviewed on {formatDate(interview.scheduled_date)}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setFeedbackForm({ ...feedbackForm, interview_id: interview.interview_id });
                      setFeedbackModalOpen(true);
                    }}
                  >
                    Submit Feedback
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-muted-foreground">No pending feedback</div>
          )}
        </CardContent>
      </Card>

      {/* All Exit Interviews Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Exit Interviews</CardTitle>
              <CardDescription>Comprehensive list of all exit interviews</CardDescription>
            </div>
            <Button onClick={exportToExcel} variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export to Excel
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {allInterviews && allInterviews.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-medium">Employee</th>
                    <th className="text-left p-2 font-medium">Department</th>
                    <th className="text-left p-2 font-medium">Last Working Day</th>
                    <th className="text-left p-2 font-medium">Status</th>
                    <th className="text-left p-2 font-medium">Interview Date/Time</th>
                    <th className="text-left p-2 font-medium">Reason to Leave</th>
                    <th className="text-left p-2 font-medium">Feedback Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {allInterviews.map((interview: any) => (
                    <tr key={interview.interview_id} className="border-b hover:bg-muted/50">
                      <td className="p-2">
                        <div>
                          <p className="font-medium">{interview.employee_name}</p>
                          <p className="text-xs text-muted-foreground">{interview.employee_email}</p>
                        </div>
                      </td>
                      <td className="p-2">{interview.department}</td>
                      <td className="p-2">{interview.last_working_day}</td>
                      <td className="p-2">
                        <Badge
                          variant={
                            interview.status === 'Completed'
                              ? 'default'
                              : interview.status === 'Scheduled'
                              ? 'secondary'
                              : 'outline'
                          }
                        >
                          {interview.status}
                        </Badge>
                      </td>
                      <td className="p-2">
                        <div>
                          <p>{interview.interview_datetime}</p>
                          {interview.location && (
                            <p className="text-xs text-muted-foreground">{interview.location}</p>
                          )}
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="max-w-xs truncate" title={interview.reason_to_leave}>
                          {interview.reason_to_leave || '-'}
                        </div>
                      </td>
                      <td className="p-2">
                        <div className="max-w-xs truncate" title={interview.feedback_notes}>
                          {interview.feedback_notes || '-'}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">No exit interviews found</div>
          )}
        </CardContent>
      </Card>

      {/* Schedule Interview Modal */}
      <Dialog open={scheduleModalOpen} onOpenChange={setScheduleModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule Exit Interview</DialogTitle>
            <DialogDescription>Schedule a new exit interview</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSchedule}>
            <div className="space-y-4">
              <div>
                <Label htmlFor="date">Date *</Label>
                <Input
                  id="date"
                  type="date"
                  value={scheduleForm.scheduled_date}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, scheduled_date: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="time">Time *</Label>
                <Input
                  id="time"
                  type="time"
                  value={scheduleForm.scheduled_time}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, scheduled_time: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label htmlFor="location">Location *</Label>
                <Input
                  id="location"
                  value={scheduleForm.location}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, location: e.target.value })}
                  placeholder="Meeting Room or Virtual Link"
                  required
                />
              </div>
              <div>
                <Label htmlFor="interviewer">Interviewer *</Label>
                <Input
                  id="interviewer"
                  value={scheduleForm.interviewer}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, interviewer: e.target.value })}
                  placeholder="Interviewer Name"
                  required
                />
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setScheduleModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={scheduleInterview.isPending}>
                {scheduleInterview.isPending ? 'Scheduling...' : 'Schedule Interview'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Submit Feedback Modal */}
      <Dialog open={feedbackModalOpen} onOpenChange={setFeedbackModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Interview Feedback</DialogTitle>
            <DialogDescription>Provide feedback for the completed interview</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleFeedbackSubmit}>
            <div className="space-y-4">
              <div>
                <Label htmlFor="reason">Reason for Leaving *</Label>
                <Select
                  value={feedbackForm.reason_to_leave}
                  onValueChange={(value) => setFeedbackForm({ ...feedbackForm, reason_to_leave: value })}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select reason for leaving" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Better Opportunity">Better Opportunity</SelectItem>
                    <SelectItem value="Career Growth">Career Growth</SelectItem>
                    <SelectItem value="Relocation">Relocation</SelectItem>
                    <SelectItem value="Personal Reasons">Personal Reasons</SelectItem>
                    <SelectItem value="Salary">Salary</SelectItem>
                    <SelectItem value="Work-Life Balance">Work-Life Balance</SelectItem>
                    <SelectItem value="Company Culture">Company Culture</SelectItem>
                    <SelectItem value="Management Issues">Management Issues</SelectItem>
                    <SelectItem value="Continuing Education">Continuing Education</SelectItem>
                    <SelectItem value="Health Reasons">Health Reasons</SelectItem>
                    <SelectItem value="Retirement">Retirement</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="feedback">Interview Feedback *</Label>
                <Textarea
                  id="feedback"
                  value={feedbackForm.interview_feedback}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, interview_feedback: e.target.value })}
                  placeholder="Detailed feedback from the interview (minimum 10 characters)"
                  rows={4}
                  required
                  minLength={10}
                />
              </div>
              <div>
                <Label htmlFor="hr_notes">HR Notes (Optional)</Label>
                <Textarea
                  id="hr_notes"
                  value={feedbackForm.hr_notes}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, hr_notes: e.target.value })}
                  placeholder="Additional notes"
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setFeedbackModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitFeedback.isPending}>
                {submitFeedback.isPending ? 'Submitting...' : 'Submit Feedback'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Skip Interview Modal */}
      <Dialog open={skipModalOpen} onOpenChange={setSkipModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skip Exit Interview</DialogTitle>
            <DialogDescription>
              Skip the exit interview and send IT notification for asset collection
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Are you sure you want to skip this interview?
            </p>
            <p className="text-sm font-medium">
              This will:
            </p>
            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
              <li>Mark the exit interview as skipped</li>
              <li>Send an email to IT for asset collection immediately</li>
              <li>Update the submission status to "exit_done"</li>
              <li>Expedite the offboarding process</li>
            </ul>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSkipModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleSkip} disabled={skipInterview.isPending}>
              {skipInterview.isPending ? 'Skipping...' : 'Skip & Notify IT'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
