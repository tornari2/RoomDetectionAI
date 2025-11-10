import type { DetectedRoom, BoundingBox } from '../types/blueprint'

/**
 * Transform bounding box coordinates from normalized 0-1000 range to pixel coordinates
 * @param boundingBox - Bounding box in normalized format [x_min, y_min, x_max, y_max] (0-1000)
 * @param imageWidth - Actual width of the image in pixels
 * @param imageHeight - Actual height of the image in pixels
 * @returns Bounding box in pixel coordinates
 */
export function transformBoundingBoxToPixels(
  boundingBox: [number, number, number, number],
  imageWidth: number,
  imageHeight: number
): BoundingBox {
  const [xMinNorm, yMinNorm, xMaxNorm, yMaxNorm] = boundingBox

  // Normalize from 0-1000 range to 0-1 range
  const xMin = xMinNorm / 1000
  const yMin = yMinNorm / 1000
  const xMax = xMaxNorm / 1000
  const yMax = yMaxNorm / 1000

  // Convert to pixel coordinates
  const x = xMin * imageWidth
  const y = yMin * imageHeight
  const width = (xMax - xMin) * imageWidth
  const height = (yMax - yMin) * imageHeight

  return { x, y, width, height }
}

/**
 * Transform all detected rooms' bounding boxes to pixel coordinates
 * @param rooms - Array of detected rooms with normalized bounding boxes
 * @param imageWidth - Actual width of the image in pixels
 * @param imageHeight - Actual height of the image in pixels
 * @returns Array of rooms with pixel-coordinate bounding boxes
 */
export function transformRoomsToPixels(
  rooms: DetectedRoom[],
  imageWidth: number,
  imageHeight: number
): Array<DetectedRoom & { pixelBox: BoundingBox }> {
  return rooms.map((room) => ({
    ...room,
    pixelBox: transformBoundingBoxToPixels(room.bounding_box, imageWidth, imageHeight),
  }))
}

