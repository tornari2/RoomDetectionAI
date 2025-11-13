import { Download, FileJson } from 'lucide-react'
import styles from './ExportButtons.module.css'

interface ExportButtonsProps {
  onExportImage: () => void
  onExportJSON: () => void
  disabled?: boolean
  hasData?: boolean
}

export default function ExportButtons({
  onExportImage,
  onExportJSON,
  disabled = false,
  hasData = false,
}: ExportButtonsProps) {
  const isDisabled = disabled || !hasData

  return (
    <div className={styles.container}>
      <button
        className={styles.exportButton}
        onClick={onExportImage}
        disabled={isDisabled}
        aria-label="Export annotated image as PNG"
        title="Download annotated image with bounding boxes"
      >
        <Download size={18} />
        <span>Export Image</span>
      </button>
      
      <button
        className={styles.exportButton}
        onClick={onExportJSON}
        disabled={isDisabled}
        aria-label="Export room coordinates as JSON"
        title="Download room coordinates as JSON file"
      >
        <FileJson size={18} />
        <span>Export JSON</span>
      </button>
    </div>
  )
}

