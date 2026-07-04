import Box from '@mui/material/Box'
import CssBaseline from '@mui/material/CssBaseline'
import { ThemeProvider } from '@mui/material/styles'
import ErrorBanner from './components/ErrorBanner'
import MessageDetail from './components/MessageDetail'
import MessageList from './components/MessageList'
import SafetyBanner from './components/SafetyBanner'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import { useInbox } from './hooks/useInbox'
import { gmailTheme, surfaces, borders } from './theme'

export default function App() {
  const {
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
    setSelectedId,
    detail,
    loading,
    detailLoading,
    error,
    refresh,
    hitlAction,
  } = useInbox()

  return (
    <ThemeProvider theme={gmailTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: surfaces.canvas }}>
        <TopBar search={search} onSearchChange={setSearch} onRefresh={() => void refresh()} />
        <SafetyBanner />
        {error && <ErrorBanner message={error} onRetry={() => void refresh()} />}
        <Box
          sx={{
            display: 'flex',
            flex: 1,
            overflow: 'hidden',
            borderTop: `1px solid ${borders.panel}`,
          }}
        >
          <Sidebar
            filter={filter}
            counts={counts}
            runs={runs}
            runId={runId}
            onFilterChange={setFilter}
            onRunChange={(id) => setRunId(id === 'local' ? undefined : id)}
            onRefresh={() => void refresh()}
          />
          <MessageList
            items={items}
            selectedId={selectedId}
            loading={loading}
            onSelect={setSelectedId}
          />
          <MessageDetail
            detail={detail}
            loading={!detail && (loading || detailLoading)}
            onApprove={(m) => hitlAction('approve', m)}
            onReject={() => hitlAction('reject')}
            onSnooze={() => hitlAction('snooze')}
            onSaveEdits={(text) => hitlAction('save', text)}
          />
        </Box>
      </Box>
    </ThemeProvider>
  )
}
