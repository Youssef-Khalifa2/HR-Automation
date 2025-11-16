import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  const statusMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    submitted: 'secondary',
    leader_approved: 'default',
    leader_rejected: 'destructive',
    chm_approved: 'default',
    chm_rejected: 'destructive',
    exit_done: 'default',
    assets_recorded: 'default',
    medical_checked: 'default',
    offboarded: 'outline',
  }
  return statusMap[status] || 'secondary'
}

export function getExitInterviewStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  const statusMap: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    not_scheduled: 'secondary',
    scheduled: 'default',
    done: 'outline',
    no_show: 'destructive',
    skipped: 'destructive',
  }
  return statusMap[status] || 'secondary'
}
