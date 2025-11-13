import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import type { FileWithPreview } from '../types/file'
import { validateFile, formatFileSize } from '../utils/fileValidation'
import styles from './FileUpload.module.css'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  onProcess: (file: File) => void
  onBatchProcess?: (files: File[]) => void
  onClear?: () => void
  isProcessing?: boolean
}

export default function FileUpload({ onFileSelect, onProcess, onBatchProcess, onClear, isProcessing = false }: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<FileWithPreview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    const file = acceptedFiles[0]
    const validation = validateFile(file)

    if (!validation.isValid) {
      setError(validation.error || 'Invalid file')
      setSelectedFile(null)
      setPreview(null)
      return
    }

    setError(null)
    
    // Create preview URL for image files
    const fileWithPreview = Object.assign(file, {
      preview: URL.createObjectURL(file)
    })
    
    setSelectedFile(fileWithPreview)
    setPreview(fileWithPreview.preview)
    onFileSelect(file)
  }, [onFileSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg']
    },
    maxFiles: 1,
    multiple: false
  })

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      onDrop(Array.from(files))
    }
  }

  const handleProcess = () => {
    if (selectedFile) {
      onProcess(selectedFile)
    }
  }

  const handleClear = () => {
    if (preview) {
      URL.revokeObjectURL(preview)
    }
    setSelectedFile(null)
    setPreview(null)
    setError(null)
    // Notify parent component to clear everything
    if (onClear) {
      onClear()
    }
  }

  const handleSelectNew = () => {
    // Just trigger file input - don't clear until new file is selected
    document.getElementById('file-input-new')?.click()
  }

  const handleBatchFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const fileArray = Array.from(files)
      // Validate all files
      const invalidFiles = fileArray.filter(file => {
        const validation = validateFile(file)
        return !validation.isValid
      })
      
      if (invalidFiles.length > 0) {
        setError(`Invalid file(s): ${invalidFiles.map(f => f.name).join(', ')}`)
        return
      }
      
      setError(null)
      if (onBatchProcess) {
        onBatchProcess(fileArray)
      }
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.uploadSection}>
        {!selectedFile ? (
          <>
            <div
              {...getRootProps()}
              className={`${styles.dropzone} ${isDragActive ? styles.dropzoneActive : ''}`}
              role="button"
              aria-label="Drag and drop blueprint image or click to browse"
              tabIndex={0}
            >
              <input {...getInputProps()} aria-label="Upload blueprint image" />
              <div className={styles.dropzoneContent}>
                <svg
                  className={styles.uploadIcon}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                {isDragActive ? (
                  <p className={styles.dropzoneText}>Drop the file here...</p>
                ) : (
                  <>
                    <p className={styles.dropzoneText}>
                      Drag & drop a blueprint image here, or click to select
                    </p>
                    <p className={styles.dropzoneHint}>
                      PNG or JPG, max 50MB
                    </p>
                  </>
                )}
              </div>
            </div>
            <div className={styles.fileBrowserSection}>
              <div className={styles.buttonGroup}>
                <label htmlFor="file-input" className={styles.fileInputLabel}>
                  <span className={styles.fileInputButton}>Browse Files</span>
                  <input
                    id="file-input"
                    type="file"
                    accept="image/png,image/jpeg,image/jpg"
                    onChange={handleFileInputChange}
                    className={styles.fileInput}
                  />
                </label>
                {onBatchProcess && (
                  <label htmlFor="batch-file-input" className={styles.fileInputLabel}>
                    <span className={styles.batchFileInputButton}>Process Folder</span>
                    <input
                      id="batch-file-input"
                      type="file"
                      accept="image/png,image/jpeg,image/jpg"
                      multiple
                      onChange={handleBatchFileInputChange}
                      className={styles.fileInput}
                    />
                  </label>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className={styles.filePreviewSection}>
            <div className={styles.fileInfo}>
              <p className={styles.fileName}>{selectedFile.name}</p>
              <p className={styles.fileSize}>{formatFileSize(selectedFile.size)}</p>
            </div>
            <div className={styles.actions}>
              <button
                onClick={handleClear}
                className={styles.cancelButton}
                disabled={isProcessing}
                aria-label="Clear selected file"
              >
                Clear
              </button>
              <button
                onClick={handleSelectNew}
                className={styles.selectNewButton}
                disabled={isProcessing}
                aria-label="Select a new blueprint"
              >
                Select New
              </button>
              <button
                onClick={handleProcess}
                className={styles.processButton}
                disabled={isProcessing}
                aria-label="Start processing blueprint"
                aria-busy={isProcessing}
              >
                {isProcessing ? 'Processing...' : 'Process Blueprint'}
              </button>
            </div>
            {/* Hidden file input for "Select New" button */}
            <input
              id="file-input-new"
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              onChange={handleFileInputChange}
              style={{ display: 'none' }}
            />
          </div>
        )}
      </div>
      {error && (
        <div className={styles.errorMessage} role="alert">
          {error}
        </div>
      )}
    </div>
  )
}

