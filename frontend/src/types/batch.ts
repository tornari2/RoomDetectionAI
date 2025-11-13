import type { DetectedRoom } from './blueprint'

export interface ProcessedImage {
  file: File
  imageUrl: string
  detectedRooms: DetectedRoom[]
  blueprintId: string
  error?: string
}

export interface BatchProcessingState {
  status: 'idle' | 'processing' | 'completed' | 'error'
  currentIndex: number
  total: number
  results: ProcessedImage[]
  errors: Array<{ fileName: string; error: string }>
}

export interface BatchProcessingProgress {
  completed: number
  total: number
  currentFileName?: string
  errors: Array<{ fileName: string; error: string }>
}

