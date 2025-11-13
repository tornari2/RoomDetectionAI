export interface UploadResponse {
  blueprint_id: string
  status: 'processing'
  message: string
}

export interface StatusResponseProcessing {
  blueprint_id: string
  status: 'processing'
  message: string
}

export interface StatusResponseCompleted {
  blueprint_id: string
  status: 'completed'
  processing_time_ms: number
  detected_rooms: Array<{
    id: string
    bounding_box: [number, number, number, number]
    confidence: number
  }>
}

export interface StatusResponseFailed {
  blueprint_id: string
  status: 'failed'
  error: string
  message: string
}

export type StatusResponse = StatusResponseProcessing | StatusResponseCompleted | StatusResponseFailed

export interface ApiError {
  error: string
  message: string
  blueprint_id?: string
  details?: string
}

