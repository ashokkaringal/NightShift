import CheckIcon from '@mui/icons-material/Check'
import BlockIcon from '@mui/icons-material/Block'
import ScheduleIcon from '@mui/icons-material/Schedule'
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'

interface DraftActionsProps {
  disabled?: boolean
  onApprove: () => void
  onReject: () => void
  onSnooze: () => void
  onSaveEdits: () => void
}

const pillSx = {
  textTransform: 'none' as const,
  borderRadius: 999,
  px: 1.75,
  py: 0.5,
  fontSize: 14,
  fontWeight: 500,
  boxShadow: 'none',
}

export default function DraftActions({
  disabled = false,
  onApprove,
  onReject,
  onSnooze,
  onSaveEdits,
}: DraftActionsProps) {
  const secondarySx = {
    ...pillSx,
    bgcolor: '#fff',
    color: '#3c4043',
    borderColor: '#dadce0',
    '&:hover': { bgcolor: '#f8f9fa', borderColor: '#dadce0', boxShadow: 'none' },
  }

  return (
    <Box sx={{ display: 'flex', gap: 0.75, mt: 1.25, flexWrap: 'wrap' }}>
      <Button
        variant="contained"
        disabled={disabled}
        onClick={onApprove}
        startIcon={<CheckIcon sx={{ fontSize: 18 }} />}
        sx={{
          ...pillSx,
          bgcolor: '#1a73e8',
          '&:hover': { bgcolor: '#1765cc', boxShadow: 'none' },
        }}
      >
        Approve draft
      </Button>
      <Button variant="outlined" disabled={disabled} onClick={onReject} startIcon={<BlockIcon sx={{ fontSize: 18 }} />} sx={secondarySx}>
        Reject
      </Button>
      <Button variant="outlined" disabled={disabled} onClick={onSnooze} startIcon={<ScheduleIcon sx={{ fontSize: 18 }} />} sx={secondarySx}>
        Snooze
      </Button>
      <Button variant="outlined" disabled={disabled} onClick={onSaveEdits} startIcon={<SaveOutlinedIcon sx={{ fontSize: 18 }} />} sx={secondarySx}>
        Save edits
      </Button>
    </Box>
  )
}
