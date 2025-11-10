import { useEffect, useRef, useState } from 'react'
import type { DetectedRoom } from '../types/blueprint'
import { renderBoundingBoxes } from '../utils/canvasRenderer'
import { exportAnnotatedImage } from '../utils/imageExporter'
import { exportJSON } from '../utils/jsonExporter'
import ExportButtons from './ExportButtons'
import styles from './BlueprintDisplay.module.css'

interface BlueprintDisplayProps {
  imageUrl: string | null
  detectedRooms: DetectedRoom[]
  isLoading?: boolean
  blueprintId?: string
}

export default function BlueprintDisplay({
  imageUrl,
  detectedRooms,
  isLoading = false,
  blueprintId,
}: BlueprintDisplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement | null>(null)
  const [imageDimensions, setImageDimensions] = useState<{ width: number; height: number } | null>(null)
  const [imageError, setImageError] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  // Export handlers
  const handleExportImage = async () => {
    if (!imageRef.current || detectedRooms.length === 0) {
      setExportError('No data to export')
      return
    }

    try {
      setExportError(null)
      await exportAnnotatedImage(imageRef.current, detectedRooms, blueprintId)
    } catch (error) {
      console.error('Export image failed:', error)
      setExportError('Failed to export image')
    }
  }

  const handleExportJSON = () => {
    if (detectedRooms.length === 0) {
      setExportError('No data to export')
      return
    }

    try {
      setExportError(null)
      exportJSON(detectedRooms, blueprintId, imageDimensions || undefined)
    } catch (error) {
      console.error('Export JSON failed:', error)
      setExportError('Failed to export JSON')
    }
  }

  // Load image and get dimensions
  useEffect(() => {
    if (!imageUrl) {
      setImageDimensions(null)
      setImageError(null)
      return
    }

    const img = new Image()
    img.crossOrigin = 'anonymous'
    
    img.onload = () => {
      setImageDimensions({ width: img.width, height: img.height })
      setImageError(null)
      imageRef.current = img
    }

    img.onerror = () => {
      setImageError('Failed to load image')
      setImageDimensions(null)
    }

    img.src = imageUrl
  }, [imageUrl])

  // Render bounding boxes when image or rooms change
  useEffect(() => {
    if (!canvasRef.current || !imageDimensions || !imageRef.current) {
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    
    if (!ctx) {
      return
    }

    // Set canvas size to match image
    canvas.width = imageDimensions.width
    canvas.height = imageDimensions.height

    // Draw the image first
    ctx.drawImage(imageRef.current, 0, 0, imageDimensions.width, imageDimensions.height)

    // Then render bounding boxes on top
    if (detectedRooms.length > 0) {
      renderBoundingBoxes(ctx, detectedRooms, imageDimensions.width, imageDimensions.height)
    }
  }, [imageDimensions, detectedRooms])

  if (!imageUrl) {
    return (
      <div className={styles.container}>
        <div className={styles.placeholder}>
          <p>No blueprint image to display</p>
        </div>
      </div>
    )
  }

  if (imageError) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <p>{imageError}</p>
        </div>
      </div>
    )
  }

  if (isLoading || !imageDimensions) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <p>Loading blueprint...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.imageWrapper}>
        <canvas
          ref={canvasRef}
          className={styles.canvas}
          style={{
            width: imageDimensions.width,
            maxWidth: '100%',
            height: 'auto',
          }}
        />
      </div>
      {detectedRooms.length > 0 && (
        <>
        <div className={styles.stats}>
          <p>Detected {detectedRooms.length} room{detectedRooms.length !== 1 ? 's' : ''}</p>
        </div>
          <ExportButtons
            onExportImage={handleExportImage}
            onExportJSON={handleExportJSON}
            hasData={detectedRooms.length > 0}
          />
          {exportError && (
            <div className={styles.exportError}>
              <p>{exportError}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

