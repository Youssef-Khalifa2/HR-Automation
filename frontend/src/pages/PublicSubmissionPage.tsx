import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import toast, { Toaster } from 'react-hot-toast';
import { CheckCircle2 } from 'lucide-react';

const PublicSubmissionPage = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [leaders, setLeaders] = useState<Record<string, string>>({});
  const [chms, setChms] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    employee_name: '',
    employee_email: '',
    employee_id: '',
    department: '',
    leader_name: '',
    submission_date: new Date().toISOString().split('T')[0],
    last_working_day: '',
    reason: '',
    in_probation: false,
  });

  // Fetch leaders and CHMs
  useEffect(() => {
    const fetchMappings = async () => {
      try {
        const [leadersRes, chmsRes] = await Promise.all([
          axios.get('http://localhost:8000/api/mapping/leaders'),
          axios.get('http://localhost:8000/api/mapping/chms'),
        ]);
        setLeaders(leadersRes.data.leaders);
        setChms(chmsRes.data.chms);
      } catch (error) {
        console.error('Failed to fetch mappings:', error);
      }
    };
    fetchMappings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Validate required fields
      if (!formData.employee_name || !formData.employee_email || !formData.leader_name) {
        toast.error('Please fill in all required fields');
        setIsSubmitting(false);
        return;
      }

      // Submit to public API
      await axios.post('http://localhost:8000/api/submission', {
        ...formData,
        submission_date: `${formData.submission_date}T00:00:00`,
        last_working_day: `${formData.last_working_day}T00:00:00`,
      });

      setIsSuccess(true);
      toast.success('Resignation submitted successfully!');
    } catch (error: any) {
      console.error('Submission error:', error);
      toast.error(error.response?.data?.detail || 'Failed to submit resignation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle2 className="h-16 w-16 text-green-500" />
            </div>
            <CardTitle className="text-2xl">Submission Successful!</CardTitle>
            <CardDescription className="text-base mt-2">
              Your resignation has been submitted successfully. The HR team and your manager will be notified.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-sm mb-2">What happens next?</h4>
              <ul className="text-sm space-y-1 text-muted-foreground">
                <li>• Your team leader will review and approve</li>
                <li>• Your department head will provide approval</li>
                <li>• HR will schedule an exit interview</li>
                <li>• IT will process asset clearance</li>
                <li>• You'll receive updates via email</li>
              </ul>
            </div>
            <p className="text-sm text-muted-foreground text-center">
              You can close this page now.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-4">
      <Toaster position="top-right" />
      <div className="max-w-2xl mx-auto py-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Resignation Submission Form</CardTitle>
            <CardDescription>
              Please fill out this form to submit your resignation. All fields marked with * are required.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Employee Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Employee Information</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="employee_name">Full Name *</Label>
                    <Input
                      id="employee_name"
                      value={formData.employee_name}
                      onChange={(e) => handleChange('employee_name', e.target.value)}
                      placeholder="John Doe"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="employee_email">Email *</Label>
                    <Input
                      id="employee_email"
                      type="email"
                      value={formData.employee_email}
                      onChange={(e) => handleChange('employee_email', e.target.value)}
                      placeholder="john.doe@company.com"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="employee_id">CRM ID</Label>
                  <Input
                    id="employee_id"
                    value={formData.employee_id}
                    onChange={(e) => handleChange('employee_id', e.target.value)}
                    placeholder="CRM12345"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="department">Department</Label>
                    <Input
                      id="department"
                      value={formData.department}
                      onChange={(e) => handleChange('department', e.target.value)}
                      placeholder="Engineering"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="leader_name">Team Leader *</Label>
                    <Select
                      value={formData.leader_name}
                      onValueChange={(value) => handleChange('leader_name', value)}
                      required
                    >
                      <SelectTrigger id="leader_name">
                        <SelectValue placeholder="Select your team leader" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.keys(leaders).map((name) => (
                          <SelectItem key={name} value={name}>
                            {name.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Dates */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Important Dates</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="submission_date">Resignation Date *</Label>
                    <Input
                      id="submission_date"
                      type="date"
                      value={formData.submission_date}
                      onChange={(e) => handleChange('submission_date', e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="last_working_day">Last Working Day *</Label>
                    <Input
                      id="last_working_day"
                      type="date"
                      value={formData.last_working_day}
                      onChange={(e) => handleChange('last_working_day', e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Additional Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Additional Information</h3>

                <div className="space-y-2">
                  <Label htmlFor="reason">Reason for Resignation (Optional)</Label>
                  <Textarea
                    id="reason"
                    value={formData.reason}
                    onChange={(e) => handleChange('reason', e.target.value)}
                    placeholder="Please share your reason for leaving (optional)"
                    rows={4}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="in_probation"
                    checked={formData.in_probation}
                    onCheckedChange={(checked) => handleChange('in_probation', checked)}
                  />
                  <Label
                    htmlFor="in_probation"
                    className="text-sm font-normal cursor-pointer"
                  >
                    I am currently in probation period
                  </Label>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-4">
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isSubmitting}
                  size="lg"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Resignation'}
                </Button>
              </div>

              <p className="text-xs text-muted-foreground text-center">
                By submitting this form, you acknowledge that your resignation will be processed according to company policy.
              </p>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PublicSubmissionPage;
