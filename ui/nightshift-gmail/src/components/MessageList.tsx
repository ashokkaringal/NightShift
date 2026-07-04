import MarkEmailReadOutlinedIcon from '@mui/icons-material/MarkEmailReadOutlined'
import Box from '@mui/material/Box'
import Skeleton from '@mui/material/Skeleton'
import Typography from '@mui/material/Typography'
import MessageItem from './MessageItem'
import MessageListHeader from './MessageListHeader'
import { layout, surfaces, borders } from '../theme'
import type { InboxItem } from '../types'

interface MessageListProps {
  items: InboxItem[]
  selectedId: string | null
  loading: boolean
  onSelect: (id: string) => void
}

const listSx = {
  width: layout.listWidth,
  minWidth: layout.listWidth,
  maxWidth: layout.listWidth,
  flexShrink: 0,
  borderRight: `1px solid ${borders.panel}`,
  overflowY: 'auto' as const,
  bgcolor: surfaces.list,
  boxShadow: '2px 0 8px rgba(60,64,67,.04)',
}

export default function MessageList({ items, selectedId, loading, onSelect }: MessageListProps) {
  if (loading) {
    return (
      <Box sx={{ ...listSx, p: 1 }}>
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} height={36} sx={{ mb: 0.5 }} />
        ))}
      </Box>
    )
  }

  if (items.length === 0) {
    return (
      <Box
        sx={{
          ...listSx,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
          p: 2,
          color: '#80868b',
        }}
      >
        <MarkEmailReadOutlinedIcon sx={{ fontSize: 40, color: '#dadce0' }} />
        <Typography color="text.secondary" sx={{ fontSize: 13 }}>
          No messages in this view
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={listSx}>
      <MessageListHeader />
      {items.map((item) => (
        <MessageItem
          key={item.id}
          item={item}
          selected={item.id === selectedId}
          onSelect={() => onSelect(item.id)}
        />
      ))}
    </Box>
  )
}
