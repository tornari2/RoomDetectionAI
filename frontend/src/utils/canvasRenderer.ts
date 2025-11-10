import type { BoundingBox, DetectedRoom } from '../types/blueprint'

/**
 * Generate a color for a bounding box based on room ID
 * Ensures distinct colors for different rooms
 */
export function getRoomColor(roomId: string): string {
  // Simple hash function to generate consistent colors
  let hash = 0
  for (let i = 0; i < roomId.length; i++) {
    hash = roomId.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  // Generate hue from hash (0-360)
  const hue = Math.abs(hash) % 360
  
  // Use high saturation and medium lightness for visibility
  return `hsl(${hue}, 70%, 50%)`
}

/**
 * Draw a bounding box on the canvas
 */
export function drawBoundingBox(
  ctx: CanvasRenderingContext2D,
  box: BoundingBox,
  color: string,
  label?: string,
  confidence?: number
): void {
  const { x, y, width, height } = box

  // Draw rectangle
  ctx.strokeStyle = color
  ctx.lineWidth = 3
  ctx.setLineDash([])
  ctx.strokeRect(x, y, width, height)

  // Draw semi-transparent fill
  ctx.fillStyle = color
  ctx.globalAlpha = 0.2
  ctx.fillRect(x, y, width, height)
  ctx.globalAlpha = 1.0

  // Draw label background
  if (label || confidence !== undefined) {
    const labelText = label || `Confidence: ${(confidence! * 100).toFixed(1)}%`
    const padding = 4
    const fontSize = 14
    ctx.font = `${fontSize}px sans-serif`
    const textMetrics = ctx.measureText(labelText)
    const textWidth = textMetrics.width
    const textHeight = fontSize

    // Background rectangle for text
    ctx.fillStyle = color
    ctx.globalAlpha = 0.9
    ctx.fillRect(
      x,
      y - textHeight - padding * 2,
      textWidth + padding * 2,
      textHeight + padding * 2
    )

    // Text
    ctx.fillStyle = '#ffffff'
    ctx.fillText(
      labelText,
      x + padding,
      y - padding
    )
    ctx.globalAlpha = 1.0
  }
}

/**
 * Clear the canvas
 */
export function clearCanvas(ctx: CanvasRenderingContext2D, width: number, height: number): void {
  ctx.clearRect(0, 0, width, height)
}

/**
 * Render all bounding boxes on the canvas
 */
export function renderBoundingBoxes(
  ctx: CanvasRenderingContext2D,
  rooms: DetectedRoom[],
  imageWidth: number,
  imageHeight: number
): void {
  // Draw each room's bounding box
  rooms.forEach((room) => {
    const pixelBox = {
      x: (room.bounding_box[0] / 1000) * imageWidth,
      y: (room.bounding_box[1] / 1000) * imageHeight,
      width: ((room.bounding_box[2] - room.bounding_box[0]) / 1000) * imageWidth,
      height: ((room.bounding_box[3] - room.bounding_box[1]) / 1000) * imageHeight,
    }

    const color = getRoomColor(room.id)
    drawBoundingBox(ctx, pixelBox, color)
  })
}

