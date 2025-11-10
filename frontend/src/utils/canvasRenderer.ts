import type { BoundingBox, DetectedRoom } from '../types/blueprint'

/**
 * Generate a color for a bounding box based on confidence level
 * High confidence = Green, Medium = Yellow, Low = Red
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.85) {
    // High confidence: Green
    return '#10B981' // emerald-500
  } else if (confidence >= 0.70) {
    // Medium confidence: Yellow/Orange
    return '#F59E0B' // amber-500
  } else {
    // Low confidence: Red
    return '#EF4444' // red-500
  }
}

/**
 * Generate a color for a bounding box based on room ID (legacy)
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
  _confidence?: number,
  isHovered?: boolean
): void {
  const { x, y, width, height } = box

  // Draw rectangle with thicker line if hovered
  ctx.strokeStyle = color
  ctx.lineWidth = isHovered ? 5 : 3
  ctx.setLineDash([])
  ctx.strokeRect(x, y, width, height)

  // Draw semi-transparent fill (more opaque if hovered)
  ctx.fillStyle = color
  ctx.globalAlpha = isHovered ? 0.35 : 0.2
  ctx.fillRect(x, y, width, height)
  ctx.globalAlpha = 1.0

  // Draw label background (only if hovered or label provided)
  if (label) {
    const padding = 6
    const fontSize = 16
    ctx.font = `bold ${fontSize}px sans-serif`
    const textMetrics = ctx.measureText(label)
    const textWidth = textMetrics.width
    const textHeight = fontSize

    // Background rectangle for text
    ctx.fillStyle = color
    ctx.globalAlpha = 0.95
    ctx.fillRect(
      x,
      y - textHeight - padding * 2,
      textWidth + padding * 2,
      textHeight + padding * 2
    )

    // Text
    ctx.fillStyle = '#ffffff'
    ctx.globalAlpha = 1.0
    ctx.fillText(
      label,
      x + padding,
      y - padding
    )
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
 * @param hoveredRoomId - Optional room ID to highlight
 */
export function renderBoundingBoxes(
  ctx: CanvasRenderingContext2D,
  rooms: DetectedRoom[],
  imageWidth: number,
  imageHeight: number,
  hoveredRoomId?: string | null
): void {
  // Draw each room's bounding box
  rooms.forEach((room) => {
    const pixelBox = {
      x: (room.bounding_box[0] / 1000) * imageWidth,
      y: (room.bounding_box[1] / 1000) * imageHeight,
      width: ((room.bounding_box[2] - room.bounding_box[0]) / 1000) * imageWidth,
      height: ((room.bounding_box[3] - room.bounding_box[1]) / 1000) * imageHeight,
    }

    // Color-code by confidence
    const color = getConfidenceColor(room.confidence)
    
    // If this room is hovered, show label with confidence
    const isHovered = hoveredRoomId === room.id
    const label = isHovered ? `${room.id}: ${(room.confidence * 100).toFixed(1)}%` : undefined
    
    drawBoundingBox(ctx, pixelBox, color, label, undefined, isHovered)
  })
}

/**
 * Find which room (if any) is at the given coordinates
 */
export function findRoomAtPoint(
  rooms: DetectedRoom[],
  x: number,
  y: number,
  imageWidth: number,
  imageHeight: number
): DetectedRoom | null {
  // Check rooms in reverse order (drawn last = on top)
  for (let i = rooms.length - 1; i >= 0; i--) {
    const room = rooms[i]
    const box = room.bounding_box
    
    // Convert normalized coordinates to pixel coordinates
    const x_min = (box[0] / 1000) * imageWidth
    const y_min = (box[1] / 1000) * imageHeight
    const x_max = (box[2] / 1000) * imageWidth
    const y_max = (box[3] / 1000) * imageHeight
    
    // Check if point is inside bounding box
    if (x >= x_min && x <= x_max && y >= y_min && y <= y_max) {
      return room
    }
  }
  
  return null
}

