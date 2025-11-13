import { useState, useEffect } from 'react'
import { ClipLoader } from 'react-spinners'
import type { ProcessedImage, BatchProcessingProgress } from '../types/batch'
import { processBatchFiles, createZipFromProcessedImages, downloadBlob } from '../utils/batchProcessor'
import styles from './BatchProcessor.module.css'

interface BatchProcessorProps {
  files: File[]
  onComplete?: (results: ProcessedImage[]) => void
  onCancel?: () => void
}

export default function BatchProcessor({ files, onComplete, onCancel }: BatchProcessorProps) {
  const [progress, setProgress] = useState<BatchProcessingProgress>({
    completed: 0,
    total: files.length,
    errors: [],
  })
  const [isProcessing, setIsProcessing] = useState(false)
  const [isCreatingZip, setIsCreatingZip] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (files.length === 0) return

    const processFiles = async () => {
      setIsProcessing(true)
      setError(null)

      try {
        // Process all files
        const results = await processBatchFiles(files, (progressUpdate) => {
          setProgress(progressUpdate)
        })

        setIsProcessing(false)
        setIsCreatingZip(true)

        // Create ZIP file
        try {
          const zipBlob = await createZipFromProcessedImages(results)
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
          const zipFileName = `blueprints_annotated_${timestamp}.zip`
          
          downloadBlob(zipBlob, zipFileName)
          
          setIsCreatingZip(false)
          onComplete?.(results)
        } catch (zipError) {
          setIsCreatingZip(false)
          setError(
            zipError instanceof Error
              ? `Failed to create ZIP file: ${zipError.message}`
              : 'Failed to create ZIP file'
          )
        }
      } catch (err) {
        setIsProcessing(false)
        setIsCreatingZip(false)
        setError(
          err instanceof Error ? err.message : 'An error occurred during batch processing'
        )
      }
    }

    processFiles()
  }, [files, onComplete])

  const progressPercentage = progress.total > 0 ? (progress.completed / progress.total) * 100 : 0
  const hasErrors = progress.errors.length > 0

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3>Batch Processing</h3>
        {onCancel && (
          <button onClick={onCancel} className={styles.cancelButton} disabled={!isProcessing && !isCreatingZip}>
            Cancel
          </button>
        )}
      </div>

      <div className={styles.progressSection}>
        {isProcessing && (
          <>
            <div className={styles.progressBarContainer}>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <span className={styles.progressText}>
                {progress.completed} / {progress.total} files processed
              </span>
            </div>
            {progress.currentFileName && (
              <p className={styles.currentFile}>
                Processing: {progress.currentFileName}
              </p>
            )}
            <div className={styles.spinnerContainer}>
              <ClipLoader size={24} color="#4299e1" />
            </div>
          </>
        )}

        {isCreatingZip && (
          <div className={styles.creatingZip}>
            <ClipLoader size={24} color="#4299e1" />
            <p>Creating ZIP file...</p>
          </div>
        )}

        {!isProcessing && !isCreatingZip && progress.completed > 0 && (
          <div className={styles.completed}>
            <p className={styles.successMessage}>
              ✓ Processing complete! {progress.completed} file(s) processed.
            </p>
            {hasErrors && (
              <div className={styles.errorsSection}>
                <p className={styles.errorsTitle}>Errors ({progress.errors.length}):</p>
                <ul className={styles.errorsList}>
                  {progress.errors.map((err, index) => (
                    <li key={index}>
                      <strong>{err.fileName}:</strong> {err.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className={styles.errorMessage} role="alert">
          <p>{error}</p>
        </div>
      )}
    </div>
  )
}

