import AddIcon from '@mui/icons-material/Add'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined'
import DraftsOutlinedIcon from '@mui/icons-material/DraftsOutlined'
import InboxIcon from '@mui/icons-material/Inbox'
import PriorityHighIcon from '@mui/icons-material/PriorityHigh'
import ScheduleIcon from '@mui/icons-material/Schedule'
import WarningAmberIcon from '@mui/icons-material/WarningAmber'
import BlockIcon from '@mui/icons-material/Block'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import FormControl from '@mui/material/FormControl'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemText from '@mui/material/ListItemText'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import Typography from '@mui/material/Typography'
import type { ReactNode } from 'react'
import type { InboxFilter, OvernightRunOption, SidebarCounts } from '../types'
import { layout, surfaces, borders } from '../theme'

interface NavItem {
  key: InboxFilter
  label: string
  countKey?: keyof SidebarCounts
  icon: ReactNode
  tone?: 'red' | 'yellow'
}

const NAV: NavItem[] = [
  { key: 'inbox', label: 'Inbox', countKey: 'inbox', icon: <InboxIcon fontSize="small" /> },
  { key: 'staged', label: 'Staged drafts', countKey: 'staged', icon: <DraftsOutlinedIcon fontSize="small" /> },
  { key: 'urgent', label: 'Urgent (RED)', countKey: 'urgent_red', icon: <PriorityHighIcon fontSize="small" />, tone: 'red' },
  { key: 'yellow', label: 'Follow-up (YELLOW)', countKey: 'yellow', icon: <WarningAmberIcon fontSize="small" />, tone: 'yellow' },
  { key: 'approved', label: 'Approved', countKey: 'approved', icon: <CheckCircleOutlineIcon fontSize="small" /> },
  { key: 'snoozed', label: 'Snoozed', countKey: 'snoozed', icon: <ScheduleIcon fontSize="small" /> },
  { key: 'rejected', label: 'Rejected', countKey: 'rejected', icon: <BlockIcon fontSize="small" /> },
]

const TONE_COLOR: Record<string, string> = {
  red: '#d93025',
  yellow: '#e37400',
}

interface SidebarProps {
  filter: InboxFilter
  counts: SidebarCounts
  runs: OvernightRunOption[]
  runId?: string
  onFilterChange: (f: InboxFilter) => void
  onRunChange: (runId: string) => void
  onRefresh: () => void
}

export default function Sidebar({
  filter,
  counts,
  runs,
  runId,
  onFilterChange,
  onRunChange,
  onRefresh,
}: SidebarProps) {
  return (
    <Box
      sx={{
        width: layout.sidebarWidth,
        minWidth: layout.sidebarWidth,
        maxWidth: layout.sidebarWidth,
        flexShrink: 0,
        bgcolor: surfaces.sidebar,
        borderRight: `1px solid ${borders.panel}`,
        display: 'flex',
        flexDirection: 'column',
        py: 1.25,
        px: 0.75,
      }}
    >
      <Button
        variant="contained"
        startIcon={<AddIcon sx={{ fontSize: 18 }} />}
        onClick={onRefresh}
        sx={{
          mx: 0.25,
          mb: 1.5,
          py: 0.75,
          px: 1.5,
          minWidth: 0,
          alignSelf: 'stretch',
          textTransform: 'none',
          borderRadius: 3,
          boxShadow: '0 1px 2px rgba(60,64,67,.3)',
          bgcolor: '#fff',
          color: '#3c4043',
          fontSize: 13,
          fontWeight: 500,
          '&:hover': { bgcolor: '#f6fafe', boxShadow: '0 1px 3px rgba(60,64,67,.35)' },
        }}
      >
        Compose
      </Button>
      <List dense disablePadding sx={{ display: 'flex', flexDirection: 'column', gap: 0.25 }}>
        {NAV.map((item) => {
          const count = item.countKey ? counts[item.countKey] : 0
          const active = filter === item.key
          const toneColor = item.tone ? TONE_COLOR[item.tone] : '#202124'
          const iconColor = active ? '#174ea6' : item.tone ? toneColor : '#5f6368'
          return (
            <ListItemButton
              key={item.key}
              selected={active}
              onClick={() => onFilterChange(item.key)}
              sx={{
                borderRadius: 999,
                py: 0.45,
                pl: 1,
                pr: 0.75,
                gap: 0.75,
                '&.Mui-selected': { bgcolor: surfaces.navSelected, '&:hover': { bgcolor: surfaces.navSelected } },
                '&:hover': { bgcolor: active ? surfaces.navSelected : surfaces.navHover },
              }}
            >
              <Box sx={{ display: 'flex', color: iconColor, minWidth: 18, '& svg': { fontSize: 18 } }}>{item.icon}</Box>
              <ListItemText
                primary={item.label}
                slotProps={{
                  primary: {
                    sx: {
                      fontSize: 12,
                      lineHeight: 1.25,
                      fontWeight: active ? 700 : 500,
                      color: item.tone ? toneColor : active ? '#174ea6' : '#202124',
                    },
                  },
                }}
              />
              <Box
                sx={{
                  fontSize: 11,
                  fontWeight: active || count > 0 ? 700 : 400,
                  color: item.tone && count > 0 ? toneColor : '#5f6368',
                  minWidth: 14,
                  textAlign: 'right',
                  flexShrink: 0,
                }}
              >
                {count}
              </Box>
            </ListItemButton>
          )
        })}
      </List>
      <Box sx={{ mt: 'auto', px: 0.5, pt: 1.5 }}>
        <Typography
          variant="caption"
          sx={{ color: '#5f6368', display: 'block', mb: 0.5, fontWeight: 500, fontSize: 10, letterSpacing: 0.3 }}
        >
          OVERNIGHT RUN
        </Typography>
        <FormControl size="small" fullWidth>
          <Select
            value={runId ?? runs[0]?.id ?? ''}
            onChange={(e) => onRunChange(e.target.value)}
            sx={{ bgcolor: '#fff', fontSize: 11, borderRadius: 2 }}
          >
            {runs.map((r) => (
              <MenuItem key={r.id} value={r.id}>
                {r.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>
    </Box>
  )
}
