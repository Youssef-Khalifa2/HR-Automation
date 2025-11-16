import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import toast from 'react-hot-toast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Plus, Trash2, Edit, Save, X, Upload, Settings, Mail, Users } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { Navigate } from 'react-router-dom';

interface TeamMapping {
  id: number;
  team_leader_name: string;
  team_leader_email: string;
  chinese_head_name: string | null;
  chinese_head_email: string | null;
  department: string | null;
  crm: string | null;
  vendor_email: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface SystemConfig {
  id: number;
  config_key: string;
  config_value: string | null;
  config_type: string;
  category: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function AdminPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('mappings');
  const [editingMapping, setEditingMapping] = useState<TeamMapping | null>(null);
  const [newMapping, setNewMapping] = useState<Partial<TeamMapping>>({});
  const [showAddMapping, setShowAddMapping] = useState(false);

  // Email config state
  const [emailConfig, setEmailConfig] = useState({
    hr_email: '',
    hr_email_cc: '',
    it_email: '',
    email_provider: 'sendgrid',
    sendgrid_api_key: '',
    smtp_host: '',
    smtp_port: '',
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: '',
    smtp_from_name: '',
    vendor_migrate_email: '',
    vendor_justhr_email_1: '',
    vendor_justhr_email_2: '',
  });

  // System config state
  const [systemConfig, setSystemConfig] = useState({
    app_base_url: '',
    frontend_url: '',
    enable_auto_reminders: false,
    reminder_threshold_hours: '',
  });

  // Check if user is admin
  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  // Fetch team mappings
  const { data: mappings, isLoading: loadingMappings } = useQuery({
    queryKey: ['admin-mappings'],
    queryFn: async () => {
      const { data } = await api.get<TeamMapping[]>('/api/admin/mappings');
      return data;
    },
  });

  // Fetch system configs
  const { data: configs, isLoading: loadingConfigs } = useQuery({
    queryKey: ['admin-configs'],
    queryFn: async () => {
      const { data } = await api.get<SystemConfig[]>('/api/admin/config');
      return data;
    },
    onSuccess: (data) => {
      // Populate email config
      const hrEmail = data.find(c => c.config_key === 'HR_EMAIL');
      const itEmail = data.find(c => c.config_key === 'IT_EMAIL');
      const smtpHost = data.find(c => c.config_key === 'SMTP_HOST');
      const smtpPort = data.find(c => c.config_key === 'SMTP_PORT');
      const smtpFrom = data.find(c => c.config_key === 'SMTP_FROM_EMAIL');
      const smtpFromName = data.find(c => c.config_key === 'SMTP_FROM_NAME');

      // Get new config values
      const hrEmailCC = data.find(c => c.config_key === 'HR_EMAIL_CC');
      const emailProvider = data.find(c => c.config_key === 'EMAIL_PROVIDER');
      const sendgridKey = data.find(c => c.config_key === 'SENDGRID_API_KEY');
      const smtpUser = data.find(c => c.config_key === 'SMTP_USER');
      const smtpPassword = data.find(c => c.config_key === 'SMTP_PASSWORD');
      const vendorMigrate = data.find(c => c.config_key === 'VENDOR_MIGRATE_EMAIL');
      const vendorJustHR1 = data.find(c => c.config_key === 'VENDOR_JUSTHR_EMAIL_1');
      const vendorJustHR2 = data.find(c => c.config_key === 'VENDOR_JUSTHR_EMAIL_2');

      setEmailConfig({
        hr_email: hrEmail?.config_value || '',
        hr_email_cc: hrEmailCC?.config_value || '',
        it_email: itEmail?.config_value || '',
        email_provider: emailProvider?.config_value || 'sendgrid',
        sendgrid_api_key: sendgridKey?.config_value || '',
        smtp_host: smtpHost?.config_value || '',
        smtp_port: smtpPort?.config_value || '',
        smtp_user: smtpUser?.config_value || '',
        smtp_password: smtpPassword?.config_value || '',
        smtp_from_email: smtpFrom?.config_value || '',
        smtp_from_name: smtpFromName?.config_value || '',
        vendor_migrate_email: vendorMigrate?.config_value || '',
        vendor_justhr_email_1: vendorJustHR1?.config_value || '',
        vendor_justhr_email_2: vendorJustHR2?.config_value || '',
      });

      // Populate system config
      const appUrl = data.find(c => c.config_key === 'APP_BASE_URL');
      const frontendUrl = data.find(c => c.config_key === 'FRONTEND_URL');
      const reminders = data.find(c => c.config_key === 'ENABLE_AUTO_REMINDERS');
      const reminderHours = data.find(c => c.config_key === 'REMINDER_THRESHOLD_HOURS');

      setSystemConfig({
        app_base_url: appUrl?.config_value || '',
        frontend_url: frontendUrl?.config_value || '',
        enable_auto_reminders: reminders?.config_value === 'True',
        reminder_threshold_hours: reminderHours?.config_value || '',
      });
    },
  });

  // Create mapping mutation
  const createMapping = useMutation({
    mutationFn: async (mapping: Partial<TeamMapping>) => {
      const { data } = await api.post('/api/admin/mappings', mapping);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-mappings'] });
      toast.success('Mapping created successfully');
      setShowAddMapping(false);
      setNewMapping({});
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create mapping');
    },
  });

  // Update mapping mutation
  const updateMapping = useMutation({
    mutationFn: async ({ id, ...mapping }: Partial<TeamMapping> & { id: number }) => {
      const { data } = await api.put(`/api/admin/mappings/${id}`, mapping);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-mappings'] });
      toast.success('Mapping updated successfully');
      setEditingMapping(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update mapping');
    },
  });

  // Delete mapping mutation
  const deleteMapping = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/admin/mappings/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-mappings'] });
      toast.success('Mapping deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete mapping');
    },
  });

  // Import CSV mutation
  const importCSV = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/api/admin/mappings/import-csv', { replace_existing: true });
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['admin-mappings'] });
      toast.success(`CSV imported: ${data.imported_count} new, ${data.updated_count} updated`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to import CSV');
    },
  });

  // Update email config mutation
  const updateEmailConfig = useMutation({
    mutationFn: async (config: typeof emailConfig) => {
      const { data } = await api.put('/api/admin/config/bulk/email', config);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-configs'] });
      toast.success('Email configuration updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update email configuration');
    },
  });

  // Update system config mutation
  const updateSystemConfig = useMutation({
    mutationFn: async (config: typeof systemConfig) => {
      const { data } = await api.put('/api/admin/config/bulk/system', config);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-configs'] });
      toast.success('System configuration updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update system configuration');
    },
  });

  const handleSaveMapping = (mapping: TeamMapping) => {
    updateMapping.mutate(mapping);
  };

  const handleCreateMapping = () => {
    if (!newMapping.team_leader_name || !newMapping.team_leader_email) {
      toast.error('Team leader name and email are required');
      return;
    }
    createMapping.mutate(newMapping);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Admin Configuration</h1>
          <p className="text-gray-600 mt-1">Manage system settings, mappings, and configurations</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="mappings" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Team Mappings
            </TabsTrigger>
            <TabsTrigger value="email" className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Email Configuration
            </TabsTrigger>
            <TabsTrigger value="system" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              System Settings
            </TabsTrigger>
          </TabsList>

          {/* Team Mappings Tab */}
          <TabsContent value="mappings">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Team Leader Mappings</CardTitle>
                    <CardDescription>Manage team leader, CHM, and vendor email mappings</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => importCSV.mutate()} variant="outline" size="sm" disabled={importCSV.isLoading}>
                      <Upload className="mr-2 h-4 w-4" />
                      Import from CSV
                    </Button>
                    <Button onClick={() => setShowAddMapping(true)} size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Mapping
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {loadingMappings ? (
                  <div className="text-center py-8">Loading mappings...</div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Team Leader</TableHead>
                          <TableHead>Leader Email</TableHead>
                          <TableHead>Chinese Head</TableHead>
                          <TableHead>CHM Email</TableHead>
                          <TableHead>Department</TableHead>
                          <TableHead>CRM</TableHead>
                          <TableHead>Vendor Email</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {showAddMapping && (
                          <TableRow>
                            <TableCell>
                              <Input
                                placeholder="Leader name"
                                value={newMapping.team_leader_name || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, team_leader_name: e.target.value })}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                placeholder="leader@email.com"
                                value={newMapping.team_leader_email || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, team_leader_email: e.target.value })}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                placeholder="CHM name"
                                value={newMapping.chinese_head_name || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, chinese_head_name: e.target.value })}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                placeholder="chm@email.com"
                                value={newMapping.chinese_head_email || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, chinese_head_email: e.target.value })}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                placeholder="Department"
                                value={newMapping.department || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, department: e.target.value })}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                placeholder="CRM"
                                value={newMapping.crm || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, crm: e.target.value })}
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                placeholder="vendor@email.com"
                                value={newMapping.vendor_email || ''}
                                onChange={(e) => setNewMapping({ ...newMapping, vendor_email: e.target.value })}
                              />
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
                                <Button size="sm" onClick={handleCreateMapping}>
                                  <Save className="h-4 w-4" />
                                </Button>
                                <Button size="sm" variant="outline" onClick={() => { setShowAddMapping(false); setNewMapping({}); }}>
                                  <X className="h-4 w-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                        {mappings?.map((mapping) => (
                          <TableRow key={mapping.id}>
                            {editingMapping?.id === mapping.id ? (
                              <>
                                <TableCell>
                                  <Input
                                    value={editingMapping.team_leader_name}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, team_leader_name: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Input
                                    value={editingMapping.team_leader_email}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, team_leader_email: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Input
                                    value={editingMapping.chinese_head_name || ''}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, chinese_head_name: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Input
                                    value={editingMapping.chinese_head_email || ''}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, chinese_head_email: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Input
                                    value={editingMapping.department || ''}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, department: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Input
                                    value={editingMapping.crm || ''}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, crm: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Input
                                    value={editingMapping.vendor_email || ''}
                                    onChange={(e) => setEditingMapping({ ...editingMapping, vendor_email: e.target.value })}
                                  />
                                </TableCell>
                                <TableCell className="text-right">
                                  <div className="flex justify-end gap-2">
                                    <Button size="sm" onClick={() => handleSaveMapping(editingMapping)}>
                                      <Save className="h-4 w-4" />
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={() => setEditingMapping(null)}>
                                      <X className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </TableCell>
                              </>
                            ) : (
                              <>
                                <TableCell className="font-medium">{mapping.team_leader_name}</TableCell>
                                <TableCell>{mapping.team_leader_email}</TableCell>
                                <TableCell>{mapping.chinese_head_name || '-'}</TableCell>
                                <TableCell>{mapping.chinese_head_email || '-'}</TableCell>
                                <TableCell>{mapping.department || '-'}</TableCell>
                                <TableCell>{mapping.crm || '-'}</TableCell>
                                <TableCell>{mapping.vendor_email || '-'}</TableCell>
                                <TableCell className="text-right">
                                  <div className="flex justify-end gap-2">
                                    <Button size="sm" variant="outline" onClick={() => setEditingMapping(mapping)}>
                                      <Edit className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="destructive"
                                      onClick={() => {
                                        if (confirm(`Delete mapping for ${mapping.team_leader_name}?`)) {
                                          deleteMapping.mutate(mapping.id);
                                        }
                                      }}
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </TableCell>
                              </>
                            )}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Email Configuration Tab */}
          <TabsContent value="email">
            <Card>
              <CardHeader>
                <CardTitle>Email Configuration</CardTitle>
                <CardDescription>Configure email addresses and SMTP settings</CardDescription>
              </CardHeader>
              <CardContent>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    updateEmailConfig.mutate(emailConfig);
                  }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="hr_email">HR Email Address</Label>
                      <Input
                        id="hr_email"
                        type="email"
                        value={emailConfig.hr_email}
                        onChange={(e) => setEmailConfig({ ...emailConfig, hr_email: e.target.value })}
                        placeholder="hr@company.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="it_email">IT Email Address</Label>
                      <Input
                        id="it_email"
                        type="email"
                        value={emailConfig.it_email}
                        onChange={(e) => setEmailConfig({ ...emailConfig, it_email: e.target.value })}
                        placeholder="it@company.com"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="hr_email_cc">HR Email CC (Additional Recipients)</Label>
                    <Input
                      id="hr_email_cc"
                      type="text"
                      value={emailConfig.hr_email_cc}
                      onChange={(e) => setEmailConfig({ ...emailConfig, hr_email_cc: e.target.value })}
                      placeholder="manager@company.com, supervisor@company.com"
                    />
                    <p className="text-sm text-gray-500 mt-1">
                      Comma-separated email addresses to CC on HR notifications
                    </p>
                  </div>

                  <div className="border-t pt-4 mt-4">
                    <h3 className="text-lg font-medium mb-4">Email Provider</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="email_provider">Provider</Label>
                        <select
                          id="email_provider"
                          value={emailConfig.email_provider}
                          onChange={(e) => setEmailConfig({ ...emailConfig, email_provider: e.target.value })}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <option value="sendgrid">SendGrid</option>
                          <option value="smtp">SMTP</option>
                        </select>
                      </div>
                      {emailConfig.email_provider === 'sendgrid' && (
                        <div>
                          <Label htmlFor="sendgrid_api_key">SendGrid API Key</Label>
                          <Input
                            id="sendgrid_api_key"
                            type="password"
                            value={emailConfig.sendgrid_api_key}
                            onChange={(e) => setEmailConfig({ ...emailConfig, sendgrid_api_key: e.target.value })}
                            placeholder="SG.***"
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  {emailConfig.email_provider === 'smtp' && (
                    <div className="border-t pt-4 mt-4">
                      <h3 className="text-lg font-medium mb-4">SMTP Settings</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="smtp_host">SMTP Host</Label>
                          <Input
                            id="smtp_host"
                            value={emailConfig.smtp_host}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtp_host: e.target.value })}
                            placeholder="smtp.gmail.com"
                          />
                        </div>
                        <div>
                          <Label htmlFor="smtp_port">SMTP Port</Label>
                          <Input
                            id="smtp_port"
                            type="number"
                            value={emailConfig.smtp_port}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: e.target.value })}
                            placeholder="587"
                          />
                        </div>
                        <div>
                          <Label htmlFor="smtp_user">SMTP Username</Label>
                          <Input
                            id="smtp_user"
                            value={emailConfig.smtp_user}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtp_user: e.target.value })}
                            placeholder="username@example.com"
                          />
                        </div>
                        <div>
                          <Label htmlFor="smtp_password">SMTP Password</Label>
                          <Input
                            id="smtp_password"
                            type="password"
                            value={emailConfig.smtp_password}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtp_password: e.target.value })}
                            placeholder="••••••••"
                          />
                        </div>
                        <div>
                          <Label htmlFor="smtp_from_email">From Email</Label>
                          <Input
                            id="smtp_from_email"
                            type="email"
                            value={emailConfig.smtp_from_email}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtp_from_email: e.target.value })}
                            placeholder="noreply@company.com"
                          />
                        </div>
                        <div>
                          <Label htmlFor="smtp_from_name">From Name</Label>
                          <Input
                            id="smtp_from_name"
                            value={emailConfig.smtp_from_name}
                            onChange={(e) => setEmailConfig({ ...emailConfig, smtp_from_name: e.target.value })}
                            placeholder="HR Automation System"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="border-t pt-4 mt-4">
                    <h3 className="text-lg font-medium mb-4">Vendor Email Addresses</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="vendor_migrate_email">Migrate Business Email</Label>
                        <Input
                          id="vendor_migrate_email"
                          type="email"
                          value={emailConfig.vendor_migrate_email}
                          onChange={(e) => setEmailConfig({ ...emailConfig, vendor_migrate_email: e.target.value })}
                          placeholder="hrcrm@migratebusiness.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor="vendor_justhr_email_1">Just HR Email 1</Label>
                        <Input
                          id="vendor_justhr_email_1"
                          type="email"
                          value={emailConfig.vendor_justhr_email_1}
                          onChange={(e) => setEmailConfig({ ...emailConfig, vendor_justhr_email_1: e.target.value })}
                          placeholder="r.kandil@jhr-services.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor="vendor_justhr_email_2">Just HR Email 2</Label>
                        <Input
                          id="vendor_justhr_email_2"
                          type="email"
                          value={emailConfig.vendor_justhr_email_2}
                          onChange={(e) => setEmailConfig({ ...emailConfig, vendor_justhr_email_2: e.target.value })}
                          placeholder="m.khaled@jhr-services.com"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button type="submit" disabled={updateEmailConfig.isLoading}>
                      {updateEmailConfig.isLoading ? 'Saving...' : 'Save Email Configuration'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Settings Tab */}
          <TabsContent value="system">
            <Card>
              <CardHeader>
                <CardTitle>System Settings</CardTitle>
                <CardDescription>Configure application URLs and system preferences</CardDescription>
              </CardHeader>
              <CardContent>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    updateSystemConfig.mutate(systemConfig);
                  }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="app_base_url">Application Base URL</Label>
                      <Input
                        id="app_base_url"
                        value={systemConfig.app_base_url}
                        onChange={(e) => setSystemConfig({ ...systemConfig, app_base_url: e.target.value })}
                        placeholder="http://localhost:8000"
                      />
                    </div>
                    <div>
                      <Label htmlFor="frontend_url">Frontend URL</Label>
                      <Input
                        id="frontend_url"
                        value={systemConfig.frontend_url}
                        onChange={(e) => setSystemConfig({ ...systemConfig, frontend_url: e.target.value })}
                        placeholder="http://localhost:5173"
                      />
                    </div>
                  </div>

                  <div className="border-t pt-4 mt-4">
                    <h3 className="text-lg font-medium mb-4">Reminder Settings</h3>
                    <div className="space-y-4">
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="enable_auto_reminders"
                          checked={systemConfig.enable_auto_reminders}
                          onChange={(e) => setSystemConfig({ ...systemConfig, enable_auto_reminders: e.target.checked })}
                          className="h-4 w-4"
                        />
                        <Label htmlFor="enable_auto_reminders">Enable Automated Reminders</Label>
                      </div>
                      <div>
                        <Label htmlFor="reminder_threshold_hours">Reminder Threshold (hours)</Label>
                        <Input
                          id="reminder_threshold_hours"
                          type="number"
                          value={systemConfig.reminder_threshold_hours}
                          onChange={(e) => setSystemConfig({ ...systemConfig, reminder_threshold_hours: e.target.value })}
                          placeholder="24"
                        />
                        <p className="text-sm text-gray-500 mt-1">Hours before sending the first reminder</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <Button type="submit" disabled={updateSystemConfig.isLoading}>
                      {updateSystemConfig.isLoading ? 'Saving...' : 'Save System Settings'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
