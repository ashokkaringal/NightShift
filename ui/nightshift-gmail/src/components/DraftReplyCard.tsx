import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import ReplyIcon from '@mui/icons-material/Reply'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useEffect, useState } from 'react'
import DraftActions from './DraftActions'
import { statusChipStyles, borders, surfaces } from '../theme'
import type { InboxDetail } from '../types'

interface DraftReplyCardProps {
  detail: InboxDetail
  onApprove: (manager: string) => Promise<void>
  onReject: () => Promise<void>
  onSnooze: () => Promise<void>
  onSaveEdits: (text: string) => Promise<void>
}

export default function DraftReplyCard({
  detail,
  onApprove,
  onReject,
  onSnooze,
  onSaveEdits,
}: DraftReplyCardProps) {
  const [draftText, setDraftText] = useState(detail.draft_text ?? '')
  const [acting, setActing] = useState(false)
  const manager = detail.manager_name ?? 'Maria Santos'

  useEffect(() => {
    setDraftText(detail.draft_text ?? '')
  }, [detail.id, detail.draft_text])

  if (detail.kind === 'failed') {
    return (
      <Box
        sx={{
          border: '1px solid #f9ab00',
          borderLeft: '4px solid #f9ab00',
          borderRadius: 2.5,
          p: 2.5,
          mt: 3,
          bgcolor: '#fffbf0',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <ErrorOutlineIcon sx={{ fontSize: 20, color: '#e37400' }} />
          <Typography sx={{ fontWeight: 600, color: '#e37400' }}>Processing failed</Typography>
          <Chip
            label="FAILED"
            size="small"
            sx={{ ml: 'auto', height: 22, fontSize: 11, fontWeight: 700, bgcolor: '#fef7e0', color: '#e37400' }}
          />
        </Box>
        <Typography sx={{ fontSize: 14, color: '#5f6368' }}>{detail.error_detail}</Typography>
      </Box>
    )
  }

  if (detail.kind !== 'draft' && !detail.draft_text) {
    return null
  }

  const statusKey = detail.status ?? 'staged'
  const requiresHitl = detail.requires_hitl ?? true
  const chipKey =
    statusKey === 'approved' || statusKey === 'rejected' || statusKey === 'snoozed'
      ? statusKey
      : requiresHitl
        ? statusKey
        : 'no_reply'
  const chip = statusChipStyles[chipKey] ?? statusChipStyles.staged
  const canAct = requiresHitl && (statusKey === 'staged' || statusKey === 'snoozed')

  const runAction = async (fn: () => Promise<void>) => {
    setActing(true)
    try {
      await fn()
    } finally {
      setActing(false)
    }
  }

  return (
    <Box
      sx={{
        border: `1px solid ${borders.section}`,
        borderRadius: 1.5,
        mt: 1.25,
        bgcolor: surfaces.detailCard,
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 0.75,
          px: 1.5,
          py: 1,
          bgcolor: surfaces.listHeader,
          borderBottom: `1px solid ${borders.section}`,
        }}
      >
        <ReplyIcon sx={{ fontSize: 17, color: '#1a73e8', transform: 'scaleX(-1)' }} />
        <Typography sx={{ fontWeight: 600, fontSize: 14.5, color: '#202124' }}>
          NightShift draft reply
        </Typography>
        <Chip
          label={chip.label}
          size="small"
          sx={{
            ml: 'auto',
            height: 22,
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: 0.3,
            bgcolor: chip.bg,
            color: chip.color,
            borderRadius: 1.5,
          }}
        />
      </Box>

      <Box sx={{ p: 1.5 }}>
        {requiresHitl ? (
          <TextField
            multiline
            minRows={4}
            maxRows={8}
            fullWidth
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            disabled={!canAct || acting}
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: '#fff',
                borderRadius: 1.5,
                fontSize: 14,
                lineHeight: 1.55,
                color: '#3c4043',
                alignItems: 'flex-start',
                py: 0.75,
                '& fieldset': { borderColor: '#dadce0' },
                '&:hover fieldset': { borderColor: '#bdc1c6' },
                '&.Mui-focused fieldset': { borderColor: '#1a73e8', borderWidth: 2 },
              },
            }}
          />
        ) : (
          <Box
            sx={{
              bgcolor: '#f2faf4',
              border: '1px solid #cfe9d6',
              borderRadius: 1.5,
              px: 1.25,
              py: 1,
            }}
          >
            <Typography sx={{ fontSize: 14, color: '#137333', lineHeight: 1.55 }}>
              {draftText || 'No tenant reply drafted — GREEN priority per NightShift policy.'}
            </Typography>
          </Box>
        )}

        {canAct && (
          <DraftActions
            disabled={acting}
            onApprove={() => runAction(() => onApprove(manager))}
            onReject={() => runAction(onReject)}
            onSnooze={() => runAction(onSnooze)}
            onSaveEdits={() => runAction(() => onSaveEdits(draftText))}
          />
        )}

        {statusKey === 'approved' && detail.approved_by ? (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 0.75,
              mt: 1.25,
              p: 1,
              borderRadius: 1.5,
              bgcolor: '#e6f4ea',
            }}
          >
            <CheckCircleOutlinedIcon sx={{ fontSize: 16, color: '#137333', mt: 0.1 }} />
            <Box>
              <Typography sx={{ fontSize: 13, color: '#137333', fontWeight: 600 }}>
                Approved by {detail.approved_by}
                {detail.approved_at ? (
                  <Box component="span" sx={{ color: '#5f6368', fontWeight: 400 }}> at {detail.approved_at}</Box>
                ) : null}
              </Typography>
              <Typography sx={{ mt: 0.25, fontSize: 12, color: '#5f6368' }}>
                Manager sign-off recorded — outbound send remains disabled in phase 1 (no send path exists).
              </Typography>
            </Box>
          </Box>
        ) : statusKey === 'rejected' ? (
          <Typography sx={{ mt: 1.25, fontSize: 13, color: '#c5221f', fontWeight: 500 }}>
            Rejected — this draft will not be sent.
          </Typography>
        ) : statusKey === 'snoozed' ? (
          <Typography sx={{ mt: 1.25, fontSize: 13, color: '#5f6368' }}>
            Snoozed — revisit this draft later.
          </Typography>
        ) : requiresHitl ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 1.25 }}>
            <LockOutlinedIcon sx={{ fontSize: 15, color: '#80868b' }} />
            <Typography sx={{ fontSize: 12, color: '#80868b' }}>
              Approving marks the draft ready — outbound send remains disabled in phase 1.
            </Typography>
          </Box>
        ) : (
          <Typography sx={{ mt: 1.25, fontSize: 12, color: '#80868b' }}>
            GREEN priority — logged for records only. No tenant reply or manager approval needed.
          </Typography>
        )}
      </Box>
    </Box>
  )
}
