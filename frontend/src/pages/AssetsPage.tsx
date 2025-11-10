import { useState } from 'react';
import {
  useAssets,
  useCreateOrUpdateAsset,
  useApproveAsset,
  usePendingAssetApprovals,
} from '../hooks/useAssets';
import { useSubmissions } from '../hooks/useSubmissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { formatDate } from '../lib/utils';
import { Package, Plus, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import type { Asset, AssetCreate } from '../lib/types';

export default function AssetsPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'approved'>('all');

  const { data: submissions } = useSubmissions({});
  const { data: assets } = useAssets(
    filterStatus === 'all'
      ? {}
      : filterStatus === 'pending'
      ? { pending: true }
      : { approved: true }
  );
  const { data: pendingApprovals } = usePendingAssetApprovals();

  const createOrUpdateAsset = useCreateOrUpdateAsset();
  const approveAsset = useApproveAsset();

  const [assetForm, setAssetForm] = useState<AssetCreate>({
    laptop_serial: '',
    laptop_model: '',
    mouse: false,
    keyboard: false,
    headphones: false,
    monitor: false,
    monitor_serial: '',
    other_items: '',
    collection_status: 'pending',
    collected_date: null,
    collected_by: '',
    it_approval_status: 'pending',
    notes: '',
  });

  const handleCreateAsset = () => {
    if (!selectedSubmissionId) return;

    createOrUpdateAsset.mutate(
      { submission_id: selectedSubmissionId, asset: assetForm },
      {
        onSuccess: () => {
          setCreateModalOpen(false);
          setSelectedSubmissionId(null);
          resetForm();
        },
      }
    );
  };

  const handleApprove = (assetId: number) => {
    if (confirm('Approve asset clearance?')) {
      approveAsset.mutate(assetId);
    }
  };

  const resetForm = () => {
    setAssetForm({
      laptop_serial: '',
      laptop_model: '',
      mouse: false,
      keyboard: false,
      headphones: false,
      monitor: false,
      monitor_serial: '',
      other_items: '',
      collection_status: 'pending',
      collected_date: null,
      collected_by: '',
      it_approval_status: 'pending',
      notes: '',
    });
  };

  const openCreateModal = (submissionId: number) => {
    setSelectedSubmissionId(submissionId);
    setCreateModalOpen(true);
  };

  const getCollectionStatusBadge = (status: string) => {
    switch (status) {
      case 'collected':
        return <Badge className="bg-green-600">Collected</Badge>;
      case 'pending':
        return <Badge className="bg-orange-600">Pending</Badge>;
      case 'partial':
        return <Badge className="bg-blue-600">Partial</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const getITApprovalBadge = (status: string) => {
    switch (status) {
      case 'approved':
        return <Badge className="bg-green-600">Approved</Badge>;
      case 'pending':
        return <Badge className="bg-orange-600">Pending</Badge>;
      case 'rejected':
        return <Badge className="bg-red-600">Rejected</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const pendingCount = pendingApprovals?.length || 0;
  const approvedCount = assets?.filter((a) => a.it_approval_status === 'approved').length || 0;
  const totalAssets = assets?.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Asset Management</h1>
          <p className="text-muted-foreground">Track and manage company assets during offboarding</p>
        </div>
        <Button onClick={() => setCreateModalOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Record Assets
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Assets</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalAssets}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Approved</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{approvedCount}</div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approvals */}
      {pendingApprovals && pendingApprovals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              Pending Asset Approvals
            </CardTitle>
            <CardDescription>Assets awaiting IT approval</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingApprovals.map((asset) => (
                <div key={asset.id} className="flex items-center justify-between border-b pb-2 last:border-0">
                  <div>
                    <p className="font-medium">{asset.submission?.employee_name}</p>
                    <p className="text-sm text-muted-foreground">
                      Laptop: {asset.laptop_model} ({asset.laptop_serial})
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {getCollectionStatusBadge(asset.collection_status)}
                    </p>
                  </div>
                  <Button size="sm" onClick={() => handleApprove(asset.id)}>
                    Approve
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Asset List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Asset Records</CardTitle>
            <Select value={filterStatus} onValueChange={(value: any) => setFilterStatus(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Assets</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {assets && assets.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Laptop</TableHead>
                  <TableHead>Accessories</TableHead>
                  <TableHead>Collection Status</TableHead>
                  <TableHead>IT Approval</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {assets.map((asset) => (
                  <TableRow key={asset.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{asset.submission?.employee_name}</p>
                        <p className="text-xs text-muted-foreground">{asset.submission?.employee_email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <p>{asset.laptop_model || 'N/A'}</p>
                        <p className="text-xs text-muted-foreground">{asset.laptop_serial || 'N/A'}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1 flex-wrap">
                        {asset.mouse && <Badge variant="outline">Mouse</Badge>}
                        {asset.keyboard && <Badge variant="outline">Keyboard</Badge>}
                        {asset.headphones && <Badge variant="outline">Headphones</Badge>}
                        {asset.monitor && <Badge variant="outline">Monitor</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>{getCollectionStatusBadge(asset.collection_status)}</TableCell>
                    <TableCell>{getITApprovalBadge(asset.it_approval_status)}</TableCell>
                    <TableCell>
                      {asset.it_approval_status === 'pending' && (
                        <Button size="sm" variant="outline" onClick={() => handleApprove(asset.id)}>
                          Approve
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              No asset records found
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Asset Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Record Asset Information</DialogTitle>
            <DialogDescription>Document all company assets for this employee</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Submission Selection */}
            <div>
              <Label htmlFor="submission">Employee</Label>
              <Select
                value={selectedSubmissionId?.toString() || ''}
                onValueChange={(value) => setSelectedSubmissionId(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {submissions?.map((sub) => (
                    <SelectItem key={sub.id} value={sub.id.toString()}>
                      {sub.employee_name} - {sub.employee_email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Laptop Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="laptop_model">Laptop Model</Label>
                <Input
                  id="laptop_model"
                  value={assetForm.laptop_model}
                  onChange={(e) => setAssetForm({ ...assetForm, laptop_model: e.target.value })}
                  placeholder="e.g., MacBook Pro 16-inch"
                />
              </div>
              <div>
                <Label htmlFor="laptop_serial">Serial Number</Label>
                <Input
                  id="laptop_serial"
                  value={assetForm.laptop_serial}
                  onChange={(e) => setAssetForm({ ...assetForm, laptop_serial: e.target.value })}
                  placeholder="e.g., C02XYZ123456"
                />
              </div>
            </div>

            {/* Accessories */}
            <div>
              <Label>Accessories</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={assetForm.mouse}
                    onChange={(e) => setAssetForm({ ...assetForm, mouse: e.target.checked })}
                    className="rounded"
                  />
                  <span>Mouse</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={assetForm.keyboard}
                    onChange={(e) => setAssetForm({ ...assetForm, keyboard: e.target.checked })}
                    className="rounded"
                  />
                  <span>Keyboard</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={assetForm.headphones}
                    onChange={(e) => setAssetForm({ ...assetForm, headphones: e.target.checked })}
                    className="rounded"
                  />
                  <span>Headphones</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={assetForm.monitor}
                    onChange={(e) => setAssetForm({ ...assetForm, monitor: e.target.checked })}
                    className="rounded"
                  />
                  <span>Monitor</span>
                </label>
              </div>
            </div>

            {assetForm.monitor && (
              <div>
                <Label htmlFor="monitor_serial">Monitor Serial Number</Label>
                <Input
                  id="monitor_serial"
                  value={assetForm.monitor_serial}
                  onChange={(e) => setAssetForm({ ...assetForm, monitor_serial: e.target.value })}
                  placeholder="Monitor serial number"
                />
              </div>
            )}

            <div>
              <Label htmlFor="other_items">Other Items</Label>
              <Input
                id="other_items"
                value={assetForm.other_items}
                onChange={(e) => setAssetForm({ ...assetForm, other_items: e.target.value })}
                placeholder="Cables, adapters, etc."
              />
            </div>

            {/* Collection Information */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="collection_status">Collection Status</Label>
                <Select
                  value={assetForm.collection_status}
                  onValueChange={(value: any) => setAssetForm({ ...assetForm, collection_status: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="partial">Partial</SelectItem>
                    <SelectItem value="collected">Collected</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="collected_by">Collected By</Label>
                <Input
                  id="collected_by"
                  value={assetForm.collected_by}
                  onChange={(e) => setAssetForm({ ...assetForm, collected_by: e.target.value })}
                  placeholder="IT staff name"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={assetForm.notes}
                onChange={(e) => setAssetForm({ ...assetForm, notes: e.target.value })}
                placeholder="Additional notes or observations"
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setCreateModalOpen(false);
                setSelectedSubmissionId(null);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateAsset}
              disabled={createOrUpdateAsset.isPending || !selectedSubmissionId}
            >
              {createOrUpdateAsset.isPending ? 'Saving...' : 'Save Asset Record'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
