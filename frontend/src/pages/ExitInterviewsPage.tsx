import { useState } from 'react';
import {
  useUpcomingInterviews,
  usePendingFeedback,
  usePendingScheduling,
  useScheduleInterview,
  useSubmitFeedback,
  useSkipInterview,
  useExitInterviewStats,
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
import { Calendar, CheckCircle, Clock, Users } from 'lucide-react';

export default function ExitInterviewsPage() {
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [skipModalOpen, setSkipModalOpen] = useState(false);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<number | null>(null);
  const [selectedInterviewId, setSelectedInterviewId] = useState<number | null>(null);

  const { data: stats } = useExitInterviewStats();
  const { data: upcoming } = useUpcomingInterviews(30);
  const { data: pendingFeedback } = usePendingFeedback();
  const { data: pendingScheduling } = usePendingScheduling();

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
    exit_interview_id: 0,
    interview_feedback: '',
    interview_rating: 5,
    hr_notes: '',
  });

  const handleSchedule = () => {
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
    });
  };

  const handleFeedbackSubmit = () => {
    submitFeedback.mutate(feedbackForm, {
      onSuccess: () => {
        setFeedbackModalOpen(false);
        setFeedbackForm({
          exit_interview_id: 0,
          interview_feedback: '',
          interview_rating: 5,
          hr_notes: '',
        });
      },
    });
  };

  const handleSkip = () => {
    if (selectedSubmissionId) {
      skipInterview.mutate({ submission_id: selectedSubmissionId }, {
        onSuccess: () => {
          setSkipModalOpen(false);
          setSelectedSubmissionId(null);
        },
      });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Exit Interviews</h1>
        <p className="text-muted-foreground">Manage exit interview scheduling and feedback</p>
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
                <div key={submission.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{submission.employee_name}</p>
                    <p className="text-sm text-muted-foreground">{submission.employee_email}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => {
                        setScheduleForm({ ...scheduleForm, submission_id: submission.id });
                        setScheduleModalOpen(true);
                      }}
                    >
                      Schedule
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setSelectedSubmissionId(submission.id);
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
                <div key={interview.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{interview.submission?.employee_name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDate(interview.scheduled_date)} at {interview.scheduled_time}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {interview.location} | {interview.interviewer}
                    </p>
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
          <CardTitle>Pending Feedback</CardTitle>
          <CardDescription>Completed interviews awaiting feedback</CardDescription>
        </CardHeader>
        <CardContent>
          {pendingFeedback && pendingFeedback.length > 0 ? (
            <div className="space-y-3">
              {pendingFeedback.map((interview) => (
                <div key={interview.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{interview.submission?.employee_name}</p>
                    <p className="text-sm text-muted-foreground">
                      Interviewed on {formatDate(interview.scheduled_date)}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setFeedbackForm({ ...feedbackForm, exit_interview_id: interview.id });
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

      {/* Schedule Interview Modal */}
      <Dialog open={scheduleModalOpen} onOpenChange={setScheduleModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule Exit Interview</DialogTitle>
            <DialogDescription>Schedule a new exit interview</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="date">Date</Label>
              <Input
                id="date"
                type="date"
                value={scheduleForm.scheduled_date}
                onChange={(e) => setScheduleForm({ ...scheduleForm, scheduled_date: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="time">Time</Label>
              <Input
                id="time"
                type="time"
                value={scheduleForm.scheduled_time}
                onChange={(e) => setScheduleForm({ ...scheduleForm, scheduled_time: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={scheduleForm.location}
                onChange={(e) => setScheduleForm({ ...scheduleForm, location: e.target.value })}
                placeholder="Meeting Room or Virtual Link"
              />
            </div>
            <div>
              <Label htmlFor="interviewer">Interviewer</Label>
              <Input
                id="interviewer"
                value={scheduleForm.interviewer}
                onChange={(e) => setScheduleForm({ ...scheduleForm, interviewer: e.target.value })}
                placeholder="Interviewer Name"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setScheduleModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSchedule} disabled={scheduleInterview.isPending}>
              {scheduleInterview.isPending ? 'Scheduling...' : 'Schedule Interview'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Submit Feedback Modal */}
      <Dialog open={feedbackModalOpen} onOpenChange={setFeedbackModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Interview Feedback</DialogTitle>
            <DialogDescription>Provide feedback for the completed interview</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="rating">Rating (1-5)</Label>
              <Select
                value={feedbackForm.interview_rating.toString()}
                onValueChange={(value) => setFeedbackForm({ ...feedbackForm, interview_rating: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 - Poor</SelectItem>
                  <SelectItem value="2">2 - Fair</SelectItem>
                  <SelectItem value="3">3 - Good</SelectItem>
                  <SelectItem value="4">4 - Very Good</SelectItem>
                  <SelectItem value="5">5 - Excellent</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="feedback">Interview Feedback</Label>
              <Textarea
                id="feedback"
                value={feedbackForm.interview_feedback}
                onChange={(e) => setFeedbackForm({ ...feedbackForm, interview_feedback: e.target.value })}
                placeholder="Detailed feedback from the interview"
                rows={4}
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
          <DialogFooter>
            <Button variant="outline" onClick={() => setFeedbackModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleFeedbackSubmit} disabled={submitFeedback.isPending}>
              {submitFeedback.isPending ? 'Submitting...' : 'Submit Feedback'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Skip Interview Modal */}
      <Dialog open={skipModalOpen} onOpenChange={setSkipModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skip Exit Interview</DialogTitle>
            <DialogDescription>
              Skip the exit interview process for this employee
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Are you sure you want to skip this interview? This will expedite the offboarding process.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSkipModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleSkip} disabled={skipInterview.isPending}>
              {skipInterview.isPending ? 'Skipping...' : 'Skip Interview'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
