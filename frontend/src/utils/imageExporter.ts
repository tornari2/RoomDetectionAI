import type { DetectedRoom } from '../types/blueprint'
import { compositeImageWithBoxes, canvasToBlob } from './canvasCompositor'

/**
 * Generate a timestamped filename
 * @param prefix Filename prefix
 * @param extension File extension (without dot)
 * @returns Timestamped filename
 */
export function generateTimestampedFilename(prefix: string, extension: string): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
  return `${prefix}_${timestamp}.${extension}`
}

/**
 * Trigger a file download in the browser
 * @param blob The blob to download
 * @param filename The filename to save as
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  // Clean up the URL object after download
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

/**
 * Export annotated image as PNG with bounding boxes
 * @param imageElement The loaded image element
 * @param detectedRooms Array of detected rooms with bounding boxes
 * @param blueprintId Optional blueprint ID to include in filename
 */
export async function exportAnnotatedImage(
  imageElement: HTMLImageElement,
  detectedRooms: DetectedRoom[],
  blueprintId?: string
): Promise<void> {
  try {
    // Composite image with bounding boxes
    const canvas = compositeImageWithBoxes(imageElement, detectedRooms)
    
    // Convert to blob
    const blob = await canvasToBlob(canvas)
    
    // Generate filename
    const prefix = blueprintId ? `blueprint_${blueprintId}` : 'blueprint_annotated'
    const filename = generateTimestampedFilename(prefix, 'png')
    
    // Download
    downloadBlob(blob, filename)
  } catch (error) {
    console.error('Failed to export annotated image:', error)
    throw new Error('Failed to export annotated image')
  }
}

