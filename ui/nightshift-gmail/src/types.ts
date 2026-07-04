export type InboxFilter =
  | 'inbox'
  | 'staged'
  | 'urgent'
  | 'yellow'
  | 'approved'
  | 'snoozed'
  | 'rejected'
  | 'failed'

export interface InboxItem {
  id: string
  kind: 'draft' | 'failed'
  raw_item_id: string
  sender_label: string
  subject: string
  preview: string
  urgency_tier?: string | null
  status?: string | null
  approved_by?: string | null
  approved_at?: string | null
  display_time?: string | null
  run_id?: string | null
  error_detail?: string | null
}

export interface AttachmentDetail {
  filename: string
  text: string
  kind: string
}

export interface InboxDetail extends InboxItem {
  draft_text?: string | null
  summary?: string | null
  reasoning?: string | null
  tenant_email?: string | null
  sender_email?: string | null
  manager_name?: string | null
  property_label?: string | null
  raw_text?: string | null
  body_text?: string | null
  attachments?: AttachmentDetail[]
  received_at?: string | null
  requires_hitl?: boolean
}

export interface SidebarCounts {
  inbox: number
  staged: number
  urgent_red: number
  yellow: number
  approved: number
  snoozed: number
  rejected: number
}

export interface OvernightRunOption {
  id: string
  label: string
  message_count: number
}
