import { useEffect, useRef } from 'react'

interface UsePollingOptions {
  enabled: boolean
  interval: number // in milliseconds
  onPoll: () => void | Promise<void>
  onError?: (error: Error) => void
}

/**
 * Custom hook for polling an API endpoint
 * @param options - Polling configuration
 */
export function usePolling({ enabled, interval, onPoll, onError }: UsePollingOptions) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isPollingRef = useRef(false)

  useEffect(() => {
    if (!enabled) {
      // Clear interval if disabled
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      isPollingRef.current = false
      return
    }

    // Start polling immediately
    const poll = async () => {
      if (isPollingRef.current) return // Prevent overlapping polls
      
      isPollingRef.current = true
      try {
        await onPoll()
      } catch (error) {
        if (onError) {
          onError(error instanceof Error ? error : new Error('Polling error'))
        }
      } finally {
        isPollingRef.current = false
      }
    }

    // Initial poll
    poll()

    // Set up interval
    intervalRef.current = setInterval(poll, interval)

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      isPollingRef.current = false
    }
  }, [enabled, interval, onPoll, onError])
}

