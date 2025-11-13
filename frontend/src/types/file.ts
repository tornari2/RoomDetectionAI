export interface FileValidationResult {
  isValid: boolean
  error?: string
}

export interface FileWithPreview extends File {
  preview?: string
}

