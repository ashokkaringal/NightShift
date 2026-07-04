import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

import { colors, borders } from '../theme'

export default function SafetyBanner() {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1,
        bgcolor: colors.safetyBanner,
        borderBottom: `1px solid #f5c6c2`,
        borderTop: `1px solid ${borders.section}`,
        borderLeft: '4px solid #d93025',
        px: 2,
        py: 0.9,
      }}
    >
      <LockOutlinedIcon sx={{ fontSize: 16, color: '#c5221f' }} />
      <Typography sx={{ color: '#c5221f', fontSize: 13, fontWeight: 500 }}>
        NightShift drafts. It never sends — phase 1 has no outbound send path; the database enforces manager approval.
      </Typography>
    </Box>
  )
}
