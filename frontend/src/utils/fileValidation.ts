import type { FileValidationResult } from '../types/file'

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB in bytes
const ALLOWED_FILE_TYPES = ['image/png', 'image/jpeg', 'image/jpg']

export function validateFile(file: File): FileValidationResult {
  // Check file type
  if (!ALLOWED_FILE_TYPES.includes(file.type.toLowerCase())) {
    return {
      isValid: false,
      error: `Invalid file type. Only PNG and JPG files are allowed. Received: ${file.type || 'unknown'}`
    }
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
    return {
      isValid: false,
      error: `File size exceeds 50MB limit. File size: ${sizeMB}MB`
    }
  }

  return { isValid: true }
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

