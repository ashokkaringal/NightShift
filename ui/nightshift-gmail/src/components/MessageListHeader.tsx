import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { messageListGrid, borders, surfaces } from '../theme'

const headerCell = {
  fontSize: 11,
  fontWeight: 600,
  color: '#5f6368',
  letterSpacing: 0.2,
  textTransform: 'uppercase' as const,
}

export default function MessageListHeader() {
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: messageListGrid.columns,
        columnGap: messageListGrid.gap,
        alignItems: 'center',
        ...messageListGrid.headerPadding,
        borderBottom: `1px solid ${borders.section}`,
        bgcolor: surfaces.listHeader,
        position: 'sticky',
        top: 0,
        zIndex: 1,
      }}
    >
      <Box />
      <Box />
      <Typography sx={headerCell}>Sender</Typography>
      <Typography sx={headerCell}>Priority</Typography>
      <Typography sx={headerCell}>Subject</Typography>
      <Typography sx={{ ...headerCell, textAlign: 'right' }}>Response status</Typography>
      <Typography sx={{ ...headerCell, textAlign: 'right' }}>Date & time</Typography>
    </Box>
  )
}
