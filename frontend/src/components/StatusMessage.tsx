import styles from './StatusMessage.module.css'

export type StatusType = 'uploading' | 'processing' | 'completed' | 'error' | 'idle'

interface StatusMessageProps {
  status: StatusType
  message?: string
  error?: string
}

export default function StatusMessage({ status, message, error }: StatusMessageProps) {
  if (status === 'idle') {
    return null
  }

  const getStatusConfig = () => {
    switch (status) {
      case 'uploading':
        return {
          className: styles.uploading,
          defaultMessage: 'Uploading blueprint...',
          icon: '📤',
        }
      case 'processing':
        return {
          className: styles.processing,
          defaultMessage: 'Processing blueprint...',
          icon: '⚙️',
        }
      case 'completed':
        return {
          className: styles.completed,
          defaultMessage: 'Processing completed!',
          icon: '✅',
        }
      case 'error':
        return {
          className: styles.error,
          defaultMessage: 'An error occurred',
          icon: '❌',
        }
      default:
        return {
          className: styles.idle,
          defaultMessage: '',
          icon: '',
        }
    }
  }

  const config = getStatusConfig()
  const displayMessage = error || message || config.defaultMessage

  return (
    <div className={`${styles.container} ${config.className}`}>
      <span className={styles.icon}>{config.icon}</span>
      <p className={styles.message}>{displayMessage}</p>
    </div>
  )
}

