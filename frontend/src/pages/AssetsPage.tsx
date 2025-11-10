import { useState } from 'react';
import {
  useAssets,
  useCreateOrUpdateAsset,
  useMarkAssetReturned,
} from '../hooks/useAssets';
import { useSubmissions } from '../hooks/useSubmissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
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
import { Package, Plus, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import type { Asset, AssetCreate } from '../lib/types';
import toast from 'react-hot-toast';

export default function AssetsPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'returned' | 'pending'>('all');

  const { data: submissions, refetch: refetchSubmissions } = useSubmissions({});
  const { data: assets, refetch: refetchAssets } = useAssets(
    filterStatus === 'all'
      ? {}
      : filterStatus === 'returned'
      ? { returned: true }
      : { returned: false }
  );

  const handleRefresh = async () => {
    toast.promise(
      Promise.all([
        refetchSubmissions(),
        refetchAssets()
      ]),
      {
        loading: 'Refreshing assets...',
        success: 'Assets refreshed successfully',
        error: 'Failed to refresh assets'
      }
    );
  };

  const createOrUpdateAsset = useCreateOrUpdateAsset();
  const markAssetReturned = useMarkAssetReturned();

  const [assetForm, setAssetForm] = useState<AssetCreate>({
    assets_returned: false,
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

  const handleMarkReturned = (assetId: number) => {
    if (confirm('Mark assets as returned?')) {
      markAssetReturned.mutate(assetId);
    }
  };

  const resetForm = () => {
    setAssetForm({
      assets_returned: false,
      notes: '',
    });
  };

  const openCreateModal = (submissionId: number) => {
    setSelectedSubmissionId(submissionId);
    setCreateModalOpen(true);
  };

  const getStatusBadge = (returned: boolean) => {
    return returned ? (
      <Badge className="bg-green-600">Returned</Badge>
    ) : (
      <Badge className="bg-orange-600">Pending</Badge>
    );
  };

  const pendingCount = assets?.filter((a) => !a.assets_returned).length || 0;
  const returnedCount = assets?.filter((a) => a.assets_returned).length || 0;
  const totalAssets = assets?.length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Asset Management</h1>
          <p className="text-muted-foreground">Track asset returns during offboarding</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Record Asset Status
          </Button>
        </div>
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
            <CardTitle className="text-sm font-medium">Pending Return</CardTitle>
            <Clock className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Returned</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{returnedCount}</div>
          </CardContent>
        </Card>
      </div>

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
                <SelectItem value="returned">Returned</SelectItem>
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
                  <TableHead>Status</TableHead>
                  <TableHead>Notes</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {assets.map((asset) => (
                  <TableRow key={asset.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{asset.submission?.employee_name || 'N/A'}</p>
                        <p className="text-xs text-muted-foreground">{asset.submission?.employee_email || 'N/A'}</p>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(asset.assets_returned)}</TableCell>
                    <TableCell>
                      <div className="max-w-md">
                        {asset.notes || <span className="text-muted-foreground">No notes</span>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {asset.updated_at ? formatDate(asset.updated_at) : 'N/A'}
                      </span>
                    </TableCell>
                    <TableCell>
                      {!asset.assets_returned && (
                        <Button size="sm" variant="outline" onClick={() => handleMarkReturned(asset.id)}>
                          Mark Returned
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
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Record Asset Status</DialogTitle>
            <DialogDescription>Track whether assets have been returned</DialogDescription>
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

            {/* Assets Returned Checkbox */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="assets_returned"
                checked={assetForm.assets_returned}
                onChange={(e) => setAssetForm({ ...assetForm, assets_returned: e.target.checked })}
                className="rounded"
              />
              <Label htmlFor="assets_returned" className="cursor-pointer">
                Assets Returned
              </Label>
            </div>

            {/* Notes */}
            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={assetForm.notes}
                onChange={(e) => setAssetForm({ ...assetForm, notes: e.target.value })}
                placeholder="Add any notes about the assets (optional)"
                rows={4}
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
