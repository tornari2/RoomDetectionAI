import type { DetectedRoom } from '../types/blueprint'
import { generateTimestampedFilename, downloadBlob } from './imageExporter'

export interface ExportedRoomData {
  id: string
  bounding_box: {
    x_min: number
    y_min: number
    x_max: number
    y_max: number
  }
  confidence: number
}

export interface ExportedBlueprintData {
  blueprint_id?: string
  export_timestamp: string
  detected_rooms: ExportedRoomData[]
  image_dimensions?: {
    width: number
    height: number
  }
}

/**
 * Convert detected rooms to exportable format
 * @param detectedRooms Array of detected rooms
 * @returns Array of formatted room data
 */
function formatRoomsForExport(detectedRooms: DetectedRoom[]): ExportedRoomData[] {
  return detectedRooms.map((room) => ({
    id: room.id,
    bounding_box: {
      x_min: room.bounding_box[0],
      y_min: room.bounding_box[1],
      x_max: room.bounding_box[2],
      y_max: room.bounding_box[3],
    },
    confidence: room.confidence,
  }))
}

/**
 * Export detected rooms as JSON file
 * @param detectedRooms Array of detected rooms with bounding boxes
 * @param blueprintId Optional blueprint ID
 * @param imageDimensions Optional image dimensions
 */
export function exportJSON(
  detectedRooms: DetectedRoom[],
  blueprintId?: string,
  imageDimensions?: { width: number; height: number }
): void {
  try {
    // Create export data structure
    const exportData: ExportedBlueprintData = {
      blueprint_id: blueprintId,
      export_timestamp: new Date().toISOString(),
      detected_rooms: formatRoomsForExport(detectedRooms),
      image_dimensions: imageDimensions,
    }

    // Convert to JSON string with pretty formatting
    const jsonString = JSON.stringify(exportData, null, 2)
    
    // Create blob
    const blob = new Blob([jsonString], { type: 'application/json' })
    
    // Generate filename
    const prefix = blueprintId ? `blueprint_${blueprintId}_data` : 'blueprint_data'
    const filename = generateTimestampedFilename(prefix, 'json')
    
    // Download
    downloadBlob(blob, filename)
  } catch (error) {
    console.error('Failed to export JSON:', error)
    throw new Error('Failed to export JSON data')
  }
}

