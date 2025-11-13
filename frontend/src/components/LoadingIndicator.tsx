import { ClipLoader } from 'react-spinners'
import styles from './LoadingIndicator.module.css'

interface LoadingIndicatorProps {
  size?: number
  color?: string
  text?: string
}

export default function LoadingIndicator({
  size = 40,
  color = '#667eea',
  text,
}: LoadingIndicatorProps) {
  return (
    <div className={styles.container}>
      <ClipLoader size={size} color={color} />
      {text && <p className={styles.text}>{text}</p>}
    </div>
  )
}

