import { createTheme } from '@mui/material/styles'

export const gmailTheme = createTheme({
  palette: {
    primary: { main: '#1a73e8' },
    error: { main: '#d93025' },
    warning: { main: '#f9ab00' },
    success: { main: '#188038' },
    background: {
      default: '#dde3ec',
      paper: '#ffffff',
    },
    text: {
      primary: '#202124',
      secondary: '#5f6368',
    },
  },
  typography: {
    fontFamily: '"Google Sans", Roboto, Arial, sans-serif',
    fontSize: 14,
  },
  shape: { borderRadius: 8 },
})

export const colors = {
  sidebar: '#e8edf5',
  border: '#c2cdda',
  borderSoft: '#d5dbe3',
  borderRow: '#e4e8ef',
  safetyBanner: '#fce8e6',
  safetyText: '#c5221f',
  draftChip: '#1a73e8',
  hoverRow: '#eef3fb',
  selectedRow: '#d3e3fd',
  canvas: '#dde3ec',
  surface: '#ffffff',
}

/** Panel backgrounds — each major region gets a distinct tone. */
export const surfaces = {
  canvas: '#dde3ec',
  topBar: '#ffffff',
  sidebar: '#e8edf5',
  list: '#ffffff',
  listHeader: '#eef1f6',
  detail: '#f0f3f9',
  detailCard: '#ffffff',
  messageBody: '#f5f7fb',
  navHover: '#dfe6f2',
  navSelected: '#d3e3fd',
}

/** Border weights for panel edges vs row dividers. */
export const borders = {
  panel: '#c2cdda',
  section: '#d5dbe3',
  row: '#e4e8ef',
}

export interface TierToken {
  bg: string
  soft: string
  text: string
  accent: string
}

export const tierTokens: Record<string, TierToken> = {
  RED: { bg: '#fce8e6', soft: '#fef3f2', text: '#c5221f', accent: '#d93025' },
  YELLOW: { bg: '#fef7e0', soft: '#fffbf0', text: '#b06000', accent: '#f9ab00' },
  GREEN: { bg: '#e6f4ea', soft: '#f2faf4', text: '#137333', accent: '#188038' },
  SPAM: { bg: '#f1f3f4', soft: '#f8f9fa', text: '#5f6368', accent: '#9aa0a6' },
}

export const neutralTier: TierToken = {
  bg: '#f1f3f4',
  soft: '#f8f9fa',
  text: '#5f6368',
  accent: '#bdc1c6',
}

export function tierToken(tier?: string | null): TierToken {
  if (!tier) return neutralTier
  return tierTokens[tier] ?? neutralTier
}

/** Three-pane shell widths — detail grows after a readable middle list. */
export const layout = {
  sidebarWidth: 168,
  listWidth: 560,
  detailMinWidth: 420,
}

/** Shared grid for inbox header + rows (accent | checkbox | sender | priority | subject | status | time). */
export const messageListGrid = {
  columns: '3px 22px 76px 68px minmax(0, 1fr) auto 42px',
  gap: 0.5,
  rowPadding: { pl: 0, pr: 1, py: 0.65 },
  headerPadding: { pl: 0, pr: 1, py: 0.75 },
}

export const statusChipStyles: Record<string, { label: string; bg: string; color: string }> = {
  staged: { label: 'STAGED', bg: '#e8f0fe', color: '#1a73e8' },
  approved: { label: 'APPROVED', bg: '#e6f4ea', color: '#137333' },
  rejected: { label: 'REJECTED', bg: '#fce8e6', color: '#c5221f' },
  snoozed: { label: 'SNOOZED', bg: '#f1f3f4', color: '#5f6368' },
  failed: { label: 'FAILED', bg: '#fef7e0', color: '#e37400' },
  no_reply: { label: 'NO REPLY', bg: '#e6f4ea', color: '#137333' },
  draft: { label: 'DRAFT', bg: '#e8f0fe', color: '#1a73e8' },
}
