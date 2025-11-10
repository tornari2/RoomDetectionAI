import type { DetectedRoom } from '../types/blueprint'
import { getRoomColor, drawBoundingBox } from './canvasRenderer'

/**
 * Composite an image with bounding boxes drawn on a canvas
 * @param imageElement The loaded image element
 * @param detectedRooms Array of detected rooms with bounding boxes
 * @returns A canvas element with the image and bounding boxes drawn
 */
export function compositeImageWithBoxes(
  imageElement: HTMLImageElement,
  detectedRooms: DetectedRoom[]
): HTMLCanvasElement {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  if (!ctx) {
    throw new Error('Failed to get canvas context')
  }

  // Set canvas size to match image
  canvas.width = imageElement.width
  canvas.height = imageElement.height

  // Draw the image first
  ctx.drawImage(imageElement, 0, 0)

  // Draw each room's bounding box
  detectedRooms.forEach((room) => {
    const pixelBox = {
      x: (room.bounding_box[0] / 1000) * canvas.width,
      y: (room.bounding_box[1] / 1000) * canvas.height,
      width: ((room.bounding_box[2] - room.bounding_box[0]) / 1000) * canvas.width,
      height: ((room.bounding_box[3] - room.bounding_box[1]) / 1000) * canvas.height,
    }

    const color = getRoomColor(room.id)
    drawBoundingBox(ctx, pixelBox, color)
  })

  return canvas
}

/**
 * Convert a canvas to a Blob for download
 * @param canvas The canvas element to convert
 * @param mimeType The MIME type of the image (default: 'image/png')
 * @returns Promise that resolves to a Blob
 */
export function canvasToBlob(
  canvas: HTMLCanvasElement,
  mimeType: string = 'image/png'
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) {
        resolve(blob)
      } else {
        reject(new Error('Failed to convert canvas to blob'))
      }
    }, mimeType)
  })
}

