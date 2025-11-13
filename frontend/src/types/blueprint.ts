export interface DetectedRoom {
  id: string
  bounding_box: [number, number, number, number] // [x_min, y_min, x_max, y_max] in 0-1000 range
  confidence: number
}

export interface BlueprintData {
  blueprint_id: string
  detected_rooms: DetectedRoom[]
  processing_time_ms?: number
  imageUrl?: string
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

