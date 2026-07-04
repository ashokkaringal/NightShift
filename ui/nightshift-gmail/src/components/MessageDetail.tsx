import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import Paper from '@mui/material/Paper'
import Skeleton from '@mui/material/Skeleton'
import Typography from '@mui/material/Typography'
import MailOutlineIcon from '@mui/icons-material/MailOutlined'
import DraftReplyCard from './DraftReplyCard'
import { layout, tierToken, surfaces, borders } from '../theme'
import type { InboxDetail } from '../types'

function senderInitial(detail: InboxDetail): string {
  if (detail.sender_label && detail.sender_label !== 'tenant') {
    return detail.sender_label.charAt(0).toUpperCase()
  }
  const email = detail.sender_email ?? detail.tenant_email ?? ''
  if (email.includes('@')) {
    const local = email.split('@')[0]
    if (local.startsWith('tenant')) return 'T'
    return local.charAt(0).toUpperCase()
  }
  return 'T'
}

interface MessageDetailProps {
  detail: InboxDetail | null
  loading: boolean
  onApprove: (manager: string) => Promise<void>
  onReject: () => Promise<void>
  onSnooze: () => Promise<void>
  onSaveEdits: (text: string) => Promise<void>
}

const detailPaneSx = {
  flex: 1,
  minWidth: layout.detailMinWidth,
  overflowY: 'auto' as const,
  bgcolor: surfaces.detail,
  borderLeft: `1px solid ${borders.section}`,
}

export default function MessageDetail({
  detail,
  loading,
  onApprove,
  onReject,
  onSnooze,
  onSaveEdits,
}: MessageDetailProps) {
  if (loading) {
    return (
      <Box sx={{ ...detailPaneSx, p: 2 }}>
        <Paper elevation={0} sx={{ p: 2, borderRadius: 2, border: `1px solid ${borders.section}`, bgcolor: surfaces.detailCard }}>
          <Skeleton width="60%" height={32} />
          <Skeleton width="40%" sx={{ mt: 1 }} />
          <Skeleton height={120} sx={{ mt: 3 }} />
        </Paper>
      </Box>
    )
  }

  if (!detail) {
    return (
      <Box
        sx={{
          ...detailPaneSx,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1.5,
          color: '#80868b',
        }}
      >
        <MailOutlineIcon sx={{ fontSize: 56, color: '#dadce0' }} />
        <Typography color="text.secondary">Select a message to review</Typography>
      </Box>
    )
  }

  const senderEmail = detail.sender_email ?? detail.tenant_email ?? `${detail.raw_item_id}@fixture.local`
  const managerName = detail.manager_name ?? 'Maria Santos'
  const timestamp = detail.received_at ?? '—'
  const token = tierToken(detail.urgency_tier)

  return (
    <Box sx={{ ...detailPaneSx, p: 2 }}>
      <Paper
        elevation={0}
        sx={{
          borderRadius: 2,
          border: `1px solid ${borders.section}`,
          overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(60,64,67,.1)',
          bgcolor: surfaces.detailCard,
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography
            sx={{
              fontWeight: 600,
              fontSize: 18,
              color: '#202124',
              mb: 1.5,
              lineHeight: 1.3,
            }}
          >
            {detail.subject}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1.25, mb: 2 }}>
            <Avatar
              sx={{
                width: 36,
                height: 36,
                bgcolor: token.accent,
                fontSize: 15,
                fontWeight: 600,
              }}
            >
              {senderInitial(detail)}
            </Avatar>
            <Box sx={{ minWidth: 0 }}>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: 0.75 }}>
                <Typography sx={{ fontSize: 14.5, fontWeight: 600, color: '#202124' }}>
                  {senderEmail}
                </Typography>
                <Typography sx={{ fontSize: 13, color: '#5f6368' }}>to {managerName}</Typography>
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  gap: 1.25,
                  mt: 0.75,
                }}
              >
                <Typography sx={{ fontSize: 12, color: '#80868b' }}>{timestamp}</Typography>
                <Typography sx={{ fontSize: 11, color: '#9aa0a6', fontFamily: 'monospace' }}>
                  {detail.raw_item_id}
                </Typography>
                {detail.property_label && (
                  <Chip
                    label={detail.property_label}
                    size="small"
                    variant="outlined"
                    sx={{ height: 20, fontSize: 11, color: '#5f6368', borderColor: '#dadce0' }}
                  />
                )}
                {detail.urgency_tier && (
                  <Chip
                    label={detail.urgency_tier}
                    size="small"
                    sx={{
                      height: 22,
                      fontSize: 11,
                      fontWeight: 700,
                      bgcolor: token.bg,
                      color: token.text,
                      borderRadius: 1.5,
                    }}
                  />
                )}
              </Box>
            </Box>
          </Box>

          <Box
            sx={{
              bgcolor: surfaces.messageBody,
              border: `1px solid ${borders.row}`,
              borderRadius: 2,
              p: 2,
            }}
          >
            <Typography
              sx={{
                fontSize: 14,
                color: '#3c4043',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.7,
              }}
            >
              {detail.raw_text ?? detail.preview}
            </Typography>
          </Box>

          <DraftReplyCard
            detail={detail}
            onApprove={onApprove}
            onReject={onReject}
            onSnooze={onSnooze}
            onSaveEdits={onSaveEdits}
          />
        </Box>
      </Paper>
    </Box>
  )
}
