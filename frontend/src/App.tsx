import { useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import FileUpload from './components/FileUpload'
import LoadingIndicator from './components/LoadingIndicator'
import StatusMessage from './components/StatusMessage'
import BlueprintDisplay from './components/BlueprintDisplay'
import ErrorDisplay from './components/ErrorDisplay'
import type { StatusType } from './components/StatusMessage'
import type { DetectedRoom } from './types/blueprint'
import type { StatusResponseCompleted, StatusResponseFailed } from './types/api'
import { uploadBlueprint, getBlueprintStatus, ApiClientError } from './services/apiClient'
import { usePolling } from './hooks/usePolling'
import './App.css'

function App() {
  const [isProcessing, setIsProcessing] = useState(false)
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [detectedRooms, setDetectedRooms] = useState<DetectedRoom[]>([])
  const [status, setStatus] = useState<StatusType>('idle')
  const [statusMessage, setStatusMessage] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [blueprintId, setBlueprintId] = useState<string | null>(null)
  const [lastFile, setLastFile] = useState<File | null>(null)

  const handleRetry = useCallback(() => {
    if (lastFile) {
      handleProcess(lastFile)
    }
  }, [lastFile])

  const handleFileSelect = (file: File) => {
    console.log('File selected:', file.name)
    // Create preview URL for the selected file
    const url = URL.createObjectURL(file)
    setImageUrl(url)
    setDetectedRooms([]) // Clear previous results
    setStatus('idle')
    setStatusMessage('')
    setError(null)
    setBlueprintId(null)
  }

  const handleProcess = async (file: File) => {
    setLastFile(file)
    setIsProcessing(true)
    setStatus('uploading')
    setStatusMessage('Uploading blueprint...')
    setError(null)

    try {
      // Upload file to API
      const uploadResponse = await uploadBlueprint(file)
      setBlueprintId(uploadResponse.blueprint_id)
      setStatus('processing')
      setStatusMessage(uploadResponse.message || 'Processing started...')
    } catch (err) {
      console.error('Error uploading file:', err)
      setIsProcessing(false)
      setStatus('error')
      if (err instanceof ApiClientError) {
        setError(err.message)
        setStatusMessage(err.message)
      } else {
        setError('Failed to upload blueprint. Please try again.')
        setStatusMessage('Failed to upload blueprint. Please try again.')
      }
    }
  }

  // Polling function to check status
  const checkStatus = useCallback(async () => {
    if (!blueprintId) return

    try {
      const statusResponse = await getBlueprintStatus(blueprintId)

      if (statusResponse.status === 'completed') {
        const completedResponse = statusResponse as StatusResponseCompleted
        setDetectedRooms(completedResponse.detected_rooms)
        setStatus('completed')
        setStatusMessage(`Processing completed! Found ${completedResponse.detected_rooms.length} rooms in ${completedResponse.processing_time_ms}ms`)
        setIsProcessing(false)
      } else if (statusResponse.status === 'failed') {
        const failedResponse = statusResponse as StatusResponseFailed
        setStatus('error')
        setError(failedResponse.message)
        setStatusMessage(failedResponse.message)
        setIsProcessing(false)
      } else {
        // Still processing
        setStatus('processing')
        setStatusMessage(statusResponse.message || 'Processing...')
      }
    } catch (err) {
      console.error('Error checking status:', err)
      if (err instanceof ApiClientError && err.statusCode === 404) {
        // Blueprint not found - might be a temporary issue, keep polling
        return
      }
      // Other errors - stop polling and show error
      setStatus('error')
      setError(err instanceof ApiClientError ? err.message : 'Failed to check status')
      setStatusMessage(err instanceof ApiClientError ? err.message : 'Failed to check status')
      setIsProcessing(false)
    }
  }, [blueprintId])

  // Start polling when we have a blueprint ID and are processing
  usePolling({
    enabled: isProcessing && blueprintId !== null && status === 'processing',
    interval: 2500, // Poll every 2.5 seconds
    onPoll: checkStatus,
    onError: (err) => {
      console.error('Polling error:', err)
      // Don't stop polling on individual errors, but log them
    },
  })

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          <div className="app">
            <header className="app-header">
              <h1>Room Detection AI</h1>
              <p>Upload a blueprint image to detect rooms</p>
            </header>
            <main className="app-main">
              <FileUpload
                onFileSelect={handleFileSelect}
                onProcess={handleProcess}
                isProcessing={isProcessing}
              />
              {error && status === 'error' && (
                <ErrorDisplay
                  error={error}
                  onRetry={handleRetry}
                  title="Upload Failed"
                />
              )}
              <StatusMessage
                status={status}
                message={statusMessage}
                error={error || undefined}
              />
              {imageUrl && (
                <BlueprintDisplay
                  imageUrl={imageUrl}
                  detectedRooms={detectedRooms}
                  isLoading={isProcessing && status !== 'completed'}
                  blueprintId={blueprintId || undefined}
                />
              )}
              {isProcessing && status !== 'completed' && (
                <LoadingIndicator text="Processing your blueprint..." />
              )}
            </main>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  )
}

export default App
