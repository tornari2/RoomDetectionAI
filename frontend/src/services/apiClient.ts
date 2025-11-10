import type { UploadResponse, StatusResponse, ApiError } from '../types/api'

// Get API base URL from environment variable or use default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000'

export class ApiClientError extends Error {
  statusCode?: number
  apiError?: ApiError

  constructor(
    message: string,
    statusCode?: number,
    apiError?: ApiError
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.statusCode = statusCode
    this.apiError = apiError
  }
}

/**
 * Upload a blueprint image file
 */
export async function uploadBlueprint(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/blueprints/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({
        error: 'unknown_error',
        message: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new ApiClientError(errorData.message || 'Upload failed', response.status, errorData)
    }

    const data: UploadResponse = await response.json()
    return data
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }
    throw new ApiClientError(
      error instanceof Error ? error.message : 'Network error occurred',
      undefined,
      undefined
    )
  }
}

/**
 * Get the status of a blueprint processing job
 */
export async function getBlueprintStatus(blueprintId: string): Promise<StatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/blueprints/${blueprintId}/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData: ApiError = await response.json().catch(() => ({
        error: 'unknown_error',
        message: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new ApiClientError(errorData.message || 'Status check failed', response.status, errorData)
    }

    const data: StatusResponse = await response.json()
    return data
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }
    throw new ApiClientError(
      error instanceof Error ? error.message : 'Network error occurred',
      undefined,
      undefined
    )
  }
}

