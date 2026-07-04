import type {
  InboxDetail,
  InboxFilter,
  InboxItem,
  OvernightRunOption,
  SidebarCounts,
} from './types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export function fetchSidebarCounts(runId?: string): Promise<SidebarCounts> {
  const q = runId ? `?run_id=${encodeURIComponent(runId)}` : ''
  return request(`/sidebar-counts${q}`)
}

export function fetchOvernightRuns(): Promise<OvernightRunOption[]> {
  return request('/overnight-runs')
}

export function fetchInbox(
  filter: InboxFilter,
  opts?: { runId?: string; q?: string },
): Promise<InboxItem[]> {
  const params = new URLSearchParams({ filter })
  if (opts?.runId) params.set('run_id', opts.runId)
  if (opts?.q) params.set('q', opts.q)
  return request(`/inbox?${params}`)
}

export function fetchItemDetail(id: string): Promise<InboxDetail> {
  return request(`/items/${encodeURIComponent(id)}`)
}

export function approveDraft(id: string, manager: string): Promise<unknown> {
  return request(`/drafts/${encodeURIComponent(id)}/approve`, {
    method: 'POST',
    body: JSON.stringify({ manager }),
  })
}

export function rejectDraft(id: string): Promise<unknown> {
  return request(`/drafts/${encodeURIComponent(id)}/reject`, { method: 'POST' })
}

export function snoozeDraft(id: string): Promise<unknown> {
  return request(`/drafts/${encodeURIComponent(id)}/snooze`, { method: 'POST' })
}

export function saveDraft(id: string, text: string): Promise<unknown> {
  return request(`/drafts/${encodeURIComponent(id)}/save`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export function editApproveDraft(
  id: string,
  manager: string,
  text: string,
): Promise<unknown> {
  return request(`/drafts/${encodeURIComponent(id)}/edit-approve`, {
    method: 'POST',
    body: JSON.stringify({ manager, text }),
  })
}
