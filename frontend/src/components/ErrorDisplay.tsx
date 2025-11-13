import { AlertCircle, RefreshCw } from 'lucide-react'
import styles from './ErrorDisplay.module.css'

interface ErrorDisplayProps {
  error: string | Error
  onRetry?: () => void
  title?: string
}

export default function ErrorDisplay({
  error,
  onRetry,
  title = 'An error occurred',
}: ErrorDisplayProps) {
  const errorMessage = typeof error === 'string' ? error : error.message

  return (
    <div className={styles.container} role="alert" aria-live="assertive">
      <div className={styles.iconWrapper}>
        <AlertCircle className={styles.icon} size={32} />
      </div>
      <div className={styles.content}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.message}>{errorMessage}</p>
        {onRetry && (
          <button
            className={styles.retryButton}
            onClick={onRetry}
            aria-label="Retry the operation"
          >
            <RefreshCw size={18} />
            <span>Retry</span>
          </button>
        )}
      </div>
    </div>
  )
}

