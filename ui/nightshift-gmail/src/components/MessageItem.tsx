import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import Box from '@mui/material/Box'
import Checkbox from '@mui/material/Checkbox'
import Chip from '@mui/material/Chip'
import Typography from '@mui/material/Typography'
import { messageListGrid, tierToken, colors, borders } from '../theme'
import type { InboxItem } from '../types'

function StatusChip({ status, kind }: { status?: string | null; kind: string }) {
  if (kind === 'failed') {
    return (
      <Chip
        label="FAILED"
        size="small"
        sx={{ height: 18, fontSize: 9, fontWeight: 700, bgcolor: '#fef7e0', color: '#e37400' }}
      />
    )
  }
  if (status === 'approved') {
    return <CheckCircleIcon sx={{ color: '#188038', fontSize: 16 }} />
  }
  if (status === 'rejected') {
    return (
      <Chip
        label="REJECTED"
        size="small"
        sx={{ height: 18, fontSize: 9, fontWeight: 700, bgcolor: '#fce8e6', color: '#c5221f' }}
      />
    )
  }
  if (status === 'snoozed') {
    return (
      <Chip
        label="SNOOZED"
        size="small"
        sx={{ height: 18, fontSize: 9, fontWeight: 700, bgcolor: '#f1f3f4', color: '#5f6368' }}
      />
    )
  }
  return (
    <Chip
      label="DRAFT"
      size="small"
      sx={{ height: 18, fontSize: 9, fontWeight: 700, bgcolor: '#e8f0fe', color: '#1a73e8' }}
    />
  )
}

interface MessageItemProps {
  item: InboxItem
  selected: boolean
  onSelect: () => void
}

export default function MessageItem({ item, selected, onSelect }: MessageItemProps) {
  const tier = item.urgency_tier ?? ''
  const token = tierToken(tier)
  const isUnread = item.kind === 'draft' && (item.status === 'staged' || item.status === 'snoozed')

  return (
    <Box
      onClick={onSelect}
      sx={{
        display: 'grid',
        gridTemplateColumns: messageListGrid.columns,
        alignItems: 'center',
        columnGap: messageListGrid.gap,
        ...messageListGrid.rowPadding,
        cursor: 'pointer',
        borderBottom: `1px solid ${borders.row}`,
        bgcolor: selected ? colors.selectedRow : 'transparent',
        transition: 'background-color .12s',
        '&:hover': { bgcolor: selected ? colors.selectedRow : colors.hoverRow },
      }}
    >
      <Box sx={{ height: '100%', bgcolor: tier ? token.accent : 'transparent', borderRadius: 1 }} />
      <Checkbox size="small" sx={{ p: 0, '& .MuiSvgIcon-root': { fontSize: 16 } }} onClick={(e) => e.stopPropagation()} />
      <Typography
        noWrap
        sx={{
          fontSize: 13,
          fontWeight: isUnread ? 700 : 600,
          color: '#202124',
          textTransform: 'capitalize',
        }}
      >
        {item.sender_label}
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        {tier ? (
          <Chip
            label={tier}
            size="small"
            sx={{
              height: 20,
              fontSize: 9.5,
              fontWeight: 700,
              letterSpacing: 0.2,
              bgcolor: token.bg,
              color: token.text,
              minWidth: 52,
            }}
          />
        ) : null}
      </Box>
      <Typography
        noWrap
        sx={{
          minWidth: 0,
          fontSize: 13,
          color: '#3c4043',
          fontWeight: isUnread ? 500 : 400,
        }}
      >
        {item.subject}
      </Typography>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', flexShrink: 0 }}>
        <StatusChip status={item.status} kind={item.kind} />
      </Box>
      <Typography
        noWrap
        sx={{ fontSize: 11, color: '#5f6368', textAlign: 'right', flexShrink: 0 }}
      >
        {item.display_time ?? '—'}
      </Typography>
    </Box>
  )
}
