import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'

interface ErrorBannerProps {
  message: string
  onRetry: () => void
}

export default function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  return (
    <Alert
      severity="error"
      action={
        <Button color="inherit" size="small" onClick={onRetry}>
          Retry
        </Button>
      }
      sx={{ borderRadius: 0 }}
    >
      {message}
    </Alert>
  )
}
