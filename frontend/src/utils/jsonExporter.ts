import type { DetectedRoom } from '../types/blueprint'
import { generateTimestampedFilename, downloadBlob } from './imageExporter'

export interface ExportedRoomData {
  id: string
  bounding_box: [number, number, number, number] // [x_min, y_min, x_max, y_max]
  name_hint: string
}

/**
 * Generate a name hint based on room characteristics
 * @param room The detected room
 * @returns A descriptive name hint
 */
function generateNameHint(room: DetectedRoom): string {
  const bbox = room.bounding_box
  const width = bbox[2] - bbox[0]
  const height = bbox[3] - bbox[1]
  const area = width * height
  
  // Generate hints based on position and size
  const position = bbox[0] < 300 ? 'Left' : bbox[0] > 700 ? 'Right' : 'Central'
  const vertical = bbox[1] < 300 ? 'Upper' : bbox[1] > 700 ? 'Lower' : 'Middle'
  
  // Size categories
  let sizeHint = ''
  if (area < 50000) sizeHint = 'Small'
  else if (area < 150000) sizeHint = 'Medium'
  else sizeHint = 'Large'
  
  // Shape analysis
  const aspectRatio = width / height
  let shapeHint = ''
  if (aspectRatio > 1.5) shapeHint = 'Wide'
  else if (aspectRatio < 0.67) shapeHint = 'Narrow'
  else shapeHint = 'Square'
  
  return `${position} ${vertical} ${sizeHint} ${shapeHint} Space`
}

/**
 * Convert detected rooms to exportable format
 * @param detectedRooms Array of detected rooms
 * @returns Array of formatted room data
 */
function formatRoomsForExport(detectedRooms: DetectedRoom[]): ExportedRoomData[] {
  return detectedRooms.map((room) => ({
    id: room.id,
    bounding_box: room.bounding_box,
    name_hint: generateNameHint(room),
  }))
}

/**
 * Export detected rooms as JSON file
 * @param detectedRooms Array of detected rooms with bounding boxes
 * @param blueprintId Optional blueprint ID
 */
export function exportJSON(
  detectedRooms: DetectedRoom[],
  blueprintId?: string
): void {
  try {
    // Create export data in the requested format
    const exportData: ExportedRoomData[] = formatRoomsForExport(detectedRooms)

    // Convert to JSON string with pretty formatting
    const jsonString = JSON.stringify(exportData, null, 2)
    
    // Create blob
    const blob = new Blob([jsonString], { type: 'application/json' })
    
    // Generate filename
    const prefix = blueprintId ? `blueprint_${blueprintId}` : 'blueprint_rooms'
    const filename = generateTimestampedFilename(prefix, 'json')
    
    // Download
    downloadBlob(blob, filename)
  } catch (error) {
    console.error('Failed to export JSON:', error)
    throw new Error('Failed to export JSON data')
  }
}

