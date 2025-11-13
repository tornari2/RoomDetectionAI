import JSZip from 'jszip'
import type { DetectedRoom } from '../types/blueprint'
import type { ProcessedImage, BatchProcessingProgress } from '../types/batch'
import { uploadBlueprint, getBlueprintStatus } from '../services/apiClient'
import { compositeImageWithBoxes, canvasToBlob } from './canvasCompositor'
import type { StatusResponseCompleted } from '../types/api'

const CONCURRENCY_LIMIT = 5 // Match SageMaker endpoint's max_concurrency
const POLL_INTERVAL = 2000 // 2 seconds
const MAX_POLL_ATTEMPTS = 150 // 5 minutes max (150 * 2s = 300s)

/**
 * Wait for a blueprint to complete processing by polling status
 */
async function waitForCompletion(
  blueprintId: string,
  onProgress?: (message: string) => void
): Promise<StatusResponseCompleted> {
  let attempts = 0
  
  while (attempts < MAX_POLL_ATTEMPTS) {
    const status = await getBlueprintStatus(blueprintId)
    
    if (status.status === 'completed') {
      return status as StatusResponseCompleted
    }
    
    if (status.status === 'failed') {
      throw new Error(status.message || 'Processing failed')
    }
    
    // Still processing, wait and retry
    attempts++
    await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL))
    
    if (onProgress && attempts % 5 === 0) {
      onProgress(`Waiting for ${blueprintId}... (attempt ${attempts})`)
    }
  }
  
  throw new Error(`Timeout waiting for blueprint ${blueprintId} to complete`)
}

/**
 * Process a single file: upload, wait for completion, and create annotated image
 */
async function processSingleFile(
  file: File,
  onProgress?: (message: string) => void
): Promise<ProcessedImage> {
  try {
    // Upload file
    onProgress?.(`Uploading ${file.name}...`)
    const uploadResponse = await uploadBlueprint(file)
    const blueprintId = uploadResponse.blueprint_id
    
    // Wait for processing to complete
    onProgress?.(`Processing ${file.name}...`)
    const statusResponse = await waitForCompletion(blueprintId, onProgress)
    
    // Load image and create annotated version
    onProgress?.(`Creating annotated image for ${file.name}...`)
    const imageUrl = URL.createObjectURL(file)
    const imageElement = await loadImage(imageUrl)
    
    // Create canvas with bounding boxes
    const canvas = compositeImageWithBoxes(imageElement, statusResponse.detected_rooms)
    const blob = await canvasToBlob(canvas)
    
    // Clean up object URL
    URL.revokeObjectURL(imageUrl)
    
    return {
      file,
      imageUrl: URL.createObjectURL(blob),
      detectedRooms: statusResponse.detected_rooms,
      blueprintId,
    }
  } catch (error) {
    return {
      file,
      imageUrl: URL.createObjectURL(file),
      detectedRooms: [],
      blueprintId: '',
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

/**
 * Load an image from a URL and return an HTMLImageElement
 */
function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error(`Failed to load image: ${url}`))
    img.src = url
  })
}

/**
 * Process files in parallel with concurrency limiting
 */
async function processBatchWithConcurrency(
  files: File[],
  concurrency: number,
  onProgress?: (progress: BatchProcessingProgress) => void
): Promise<ProcessedImage[]> {
  const results: ProcessedImage[] = []
  const errors: Array<{ fileName: string; error: string }> = []
  let completedCount = 0
  
  // Process files in batches
  for (let i = 0; i < files.length; i += concurrency) {
    const batch = files.slice(i, i + concurrency)
    
    // Process batch in parallel
    const batchPromises = batch.map(async (file) => {
      const progressCallback = (message: string) => {
        // Progress callback during processing - show current file
        onProgress?.({
          completed: completedCount,
          total: files.length,
          currentFileName: file.name,
          errors: [...errors], // Copy array to avoid mutation issues
        })
      }
      
      const result = await processSingleFile(file, progressCallback)
      
      // Update completed count atomically
      completedCount++
      
      if (result.error) {
        errors.push({ fileName: file.name, error: result.error })
      }
      
      results.push(result)
      
      // Update progress after completion
      onProgress?.({
        completed: completedCount,
        total: files.length,
        currentFileName: undefined,
        errors: [...errors], // Copy array to avoid mutation issues
      })
      
      return result
    })
    
    // Wait for all files in this batch to complete
    await Promise.all(batchPromises)
  }
  
  return results
}

/**
 * Process a batch of files and return processed images
 */
export async function processBatchFiles(
  files: File[],
  onProgress?: (progress: BatchProcessingProgress) => void
): Promise<ProcessedImage[]> {
  if (files.length === 0) {
    return []
  }
  
  return processBatchWithConcurrency(files, CONCURRENCY_LIMIT, onProgress)
}

/**
 * Create a ZIP file from processed images
 */
export async function createZipFromProcessedImages(
  processedImages: ProcessedImage[]
): Promise<Blob> {
  const zip = new JSZip()
  const coordinatesData: Record<string, {
    blueprint_id: string
    detected_rooms: DetectedRoom[]
    original_filename: string
  }> = {}
  
  for (const processed of processedImages) {
    if (processed.error) {
      // Skip failed images, but could add error log file if needed
      continue
    }
    
    // Get the blob from the image URL
    const response = await fetch(processed.imageUrl)
    const blob = await response.blob()
    
    // Generate filename (preserve original name, add _annotated suffix)
    const originalName = processed.file.name
    const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '')
    const extension = originalName.split('.').pop() || 'png'
    const zipFileName = `${nameWithoutExt}_annotated.${extension}`
    
    // Add to ZIP
    zip.file(zipFileName, blob)
    
    // Store coordinates data for JSON file
    coordinatesData[zipFileName] = {
      blueprint_id: processed.blueprintId,
      detected_rooms: processed.detectedRooms,
      original_filename: originalName,
    }
  }
  
  // Create JSON file with bounding box coordinates
  const jsonContent = JSON.stringify(coordinatesData, null, 2)
  zip.file('bounding_boxes_coordinates.json', jsonContent)
  
  // Generate ZIP file
  return await zip.generateAsync({ type: 'blob' })
}

/**
 * Download a blob as a file
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

