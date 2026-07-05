import { useCallback, useEffect, useState } from 'react'
import {
  approveDraft,
  editApproveDraft,
  fetchInbox,
  fetchItemDetail,
  fetchOvernightRuns,
  fetchSidebarCounts,
  markSpamRead,
  rejectDraft,
  saveDraft,
  snoozeDraft,
} from '../api'
import type {
  InboxDetail,
  InboxFilter,
  InboxItem,
  OvernightRunOption,
  SidebarCounts,
} from '../types'

const EMPTY_COUNTS: SidebarCounts = {
  inbox: 0,
  staged: 0,
  urgent_red: 0,
  yellow: 0,
  spam: 0,
  spam_unread: 0,
  approved: 0,
  snoozed: 0,
  rejected: 0,
}

function resolveSelection(items: InboxItem[], preferId: string | null): string | null {
  if (items.length === 0) return null
  if (preferId && items.some((i) => i.id === preferId)) return preferId
  return items[0].id
}

export function useInbox() {
  const [filter, setFilter] = useState<InboxFilter>('inbox')
  const [search, setSearch] = useState('')
  const [runId, setRunId] = useState<string | undefined>()
  const [items, setItems] = useState<InboxItem[]>([])
  const [counts, setCounts] = useState<SidebarCounts>(EMPTY_COUNTS)
  const [runs, setRuns] = useState<OvernightRunOption[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<InboxDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(
    async (keepSelectedId?: string | null, opts?: { silent?: boolean }) => {
      if (!opts?.silent) setLoading(true)
      setError(null)
      try {
        const [inboxItems, sidebarCounts, runOptions] = await Promise.all([
          fetchInbox(filter, { runId, q: search || undefined }),
          fetchSidebarCounts(runId),
          fetchOvernightRuns(),
        ])
        setItems(inboxItems)
        setCounts(sidebarCounts)
        setRuns(runOptions)
        setSelectedId((prev) => resolveSelection(inboxItems, keepSelectedId ?? prev))
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load inbox')
      } finally {
        if (!opts?.silent) setLoading(false)
      }
    },
    [filter, runId, search],
  )

  useEffect(() => {
    void refresh()
  }, [refresh])

  const selectItem = useCallback(
    (id: string) => {
      setSelectedId(id)
      if (filter !== 'spam') return
      const item = items.find((i) => i.id === id)
      if (item?.urgency_tier !== 'SPAM') return
      void markSpamRead(id)
        .then(() => fetchSidebarCounts(runId))
        .then(setCounts)
        .catch(() => {
          /* keep current counts on failure */
        })
    },
    [filter, items, runId],
  )

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      setDetailLoading(false)
      return
    }
    let cancelled = false
    setDetailLoading(true)
    fetchItemDetail(selectedId)
      .then((d) => {
        if (!cancelled) setDetail(d)
      })
      .catch(() => {
        if (!cancelled) setDetail(null)
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [selectedId])

  const hitlAction = useCallback(
    async (
      action: 'approve' | 'reject' | 'snooze' | 'save',
      managerOrText?: string,
      text?: string,
    ) => {
      if (!selectedId || !detail || detail.kind !== 'draft' || detail.requires_hitl === false) return
      const actedId = selectedId
      try {
        if (action === 'approve' && managerOrText) {
          if (text !== undefined) {
            await editApproveDraft(actedId, managerOrText, text)
          } else {
            await approveDraft(actedId, managerOrText)
          }
        } else if (action === 'reject') {
          await rejectDraft(actedId)
        } else if (action === 'snooze') {
          await snoozeDraft(actedId)
        } else if (action === 'save' && managerOrText) {
          await saveDraft(actedId, managerOrText)
        }
        await refresh(actedId, { silent: true })
        const updated = await fetchItemDetail(actedId)
        setDetail(updated)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Action failed')
        const updated = await fetchItemDetail(actedId).catch(() => null)
        if (updated) setDetail(updated)
      }
    },
    [selectedId, detail, refresh],
  )

  return {
    filter,
    setFilter,
    search,
    setSearch,
    runId,
    setRunId,
    items,
    counts,
    runs,
    selectedId,
    selectItem,
    detail,
    loading,
    detailLoading,
    error,
    refresh,
    hitlAction,
    unreadSpam: counts.spam_unread,
  }
}
