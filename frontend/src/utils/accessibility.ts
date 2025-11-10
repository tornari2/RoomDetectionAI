/**
 * Accessibility utility functions
 */

/**
 * Announce a message to screen readers
 * @param message The message to announce
 * @param priority The priority level ('polite' or 'assertive')
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
): void {
  const announcement = document.createElement('div')
  announcement.setAttribute('role', 'status')
  announcement.setAttribute('aria-live', priority)
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message

  document.body.appendChild(announcement)

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement)
  }, 1000)
}

/**
 * Check if an element is keyboard focusable
 * @param element The element to check
 */
export function isKeyboardFocusable(element: HTMLElement): boolean {
  const tabindex = element.getAttribute('tabindex')
  if (tabindex && parseInt(tabindex) < 0) {
    return false
  }

  if (element.hasAttribute('disabled')) {
    return false
  }

  const focusableElements = [
    'a',
    'button',
    'input',
    'select',
    'textarea',
  ]

  return (
    focusableElements.includes(element.tagName.toLowerCase()) ||
    (tabindex !== null && parseInt(tabindex) >= 0)
  )
}

/**
 * Trap focus within a container (useful for modals)
 * @param container The container element
 * @returns Cleanup function
 */
export function trapFocus(container: HTMLElement): () => void {
  const focusableElements = container.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )

  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return

    if (e.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        e.preventDefault()
        lastElement?.focus()
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        e.preventDefault()
        firstElement?.focus()
      }
    }
  }

  container.addEventListener('keydown', handleKeyDown)

  // Focus first element
  firstElement?.focus()

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleKeyDown)
  }
}

/**
 * Get the accessible name of an element
 * @param element The element to check
 */
export function getAccessibleName(element: HTMLElement): string {
  // Check aria-label
  const ariaLabel = element.getAttribute('aria-label')
  if (ariaLabel) return ariaLabel

  // Check aria-labelledby
  const labelledBy = element.getAttribute('aria-labelledby')
  if (labelledBy) {
    const labelElement = document.getElementById(labelledBy)
    if (labelElement) return labelElement.textContent || ''
  }

  // Check associated label
  if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
    const id = element.getAttribute('id')
    if (id) {
      const label = document.querySelector(`label[for="${id}"]`)
      if (label) return label.textContent || ''
    }
  }

  // Fall back to text content
  return element.textContent || ''
}

/**
 * Add keyboard navigation to a list
 * @param container The container element
 * @param itemSelector CSS selector for list items
 */
export function enableKeyboardNavigation(
  container: HTMLElement,
  itemSelector: string
): () => void {
  const handleKeyDown = (e: KeyboardEvent) => {
    const items = Array.from(container.querySelectorAll<HTMLElement>(itemSelector))
    const currentIndex = items.findIndex(item => item === document.activeElement)

    if (currentIndex === -1) return

    let nextIndex = currentIndex

    switch (e.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        e.preventDefault()
        nextIndex = (currentIndex + 1) % items.length
        break
      case 'ArrowUp':
      case 'ArrowLeft':
        e.preventDefault()
        nextIndex = (currentIndex - 1 + items.length) % items.length
        break
      case 'Home':
        e.preventDefault()
        nextIndex = 0
        break
      case 'End':
        e.preventDefault()
        nextIndex = items.length - 1
        break
      default:
        return
    }

    items[nextIndex]?.focus()
  }

  container.addEventListener('keydown', handleKeyDown)

  return () => {
    container.removeEventListener('keydown', handleKeyDown)
  }
}

