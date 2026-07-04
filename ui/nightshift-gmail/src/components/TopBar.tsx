import MenuIcon from '@mui/icons-material/Menu'
import NightsStayIcon from '@mui/icons-material/NightsStay'
import RefreshIcon from '@mui/icons-material/Refresh'
import SearchIcon from '@mui/icons-material/Search'
import AppBar from '@mui/material/AppBar'
import Avatar from '@mui/material/Avatar'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import InputBase from '@mui/material/InputBase'
import Toolbar from '@mui/material/Toolbar'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { borders, surfaces } from '../theme'

interface TopBarProps {
  search: string
  onSearchChange: (value: string) => void
  onRefresh: () => void
}

export default function TopBar({ search, onSearchChange, onRefresh }: TopBarProps) {
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: surfaces.topBar,
        color: '#5f6368',
        borderBottom: `1px solid ${borders.panel}`,
        boxShadow: '0 1px 2px rgba(60,64,67,.08)',
      }}
    >
      <Toolbar sx={{ gap: 1.5, minHeight: 64, px: 2 }}>
        <IconButton edge="start" size="small" sx={{ color: '#5f6368' }}>
          <MenuIcon />
        </IconButton>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, minWidth: 150 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: '50%',
              display: 'grid',
              placeItems: 'center',
              background: 'linear-gradient(135deg, #1a73e8 0%, #6c5ce7 100%)',
              color: '#fff',
            }}
          >
            <NightsStayIcon sx={{ fontSize: 20 }} />
          </Box>
          <Typography
            sx={{ color: '#3c4043', fontWeight: 600, fontSize: 21, letterSpacing: -0.5 }}
          >
            NightShift
          </Typography>
        </Box>
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            bgcolor: '#eaf1fb',
            borderRadius: 999,
            px: 2.5,
            py: 1,
            maxWidth: 720,
            mx: 'auto',
            transition: 'background-color .15s, box-shadow .15s',
            '&:focus-within': {
              bgcolor: '#fff',
              boxShadow: '0 1px 6px rgba(32,33,36,.18)',
            },
          }}
        >
          <SearchIcon sx={{ color: '#5f6368', mr: 1.25, fontSize: 20 }} />
          <InputBase
            placeholder="Search mail"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            sx={{ flex: 1, fontSize: 14, color: '#202124' }}
            fullWidth
          />
        </Box>
        <Chip
          label="MOCK"
          size="small"
          sx={{ bgcolor: '#f1f3f4', color: '#5f6368', fontWeight: 600, letterSpacing: 0.4 }}
        />
        <Tooltip title="Refresh overnight run">
          <IconButton size="small" onClick={onRefresh} sx={{ color: '#5f6368' }}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
        <Avatar
          sx={{
            width: 34,
            height: 34,
            fontSize: 13,
            fontWeight: 600,
            bgcolor: '#6c5ce7',
          }}
        >
          PM
        </Avatar>
      </Toolbar>
    </AppBar>
  )
}
