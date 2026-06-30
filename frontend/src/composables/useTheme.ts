import { readonly, ref } from 'vue'

import { getStorageItem, setStorageItem } from '@/lib/storage'

const STORAGE_KEY = 'theme'

type Theme = 'light' | 'dark'

const theme = ref<Theme>('light')
let initialized = false

/**
 * Applies the given theme to the document root.
 *
 * @param value - The theme to apply.
 */
function applyTheme(value: Theme): void {
  theme.value = value
  document.documentElement.classList.toggle('dark', value === 'dark')
}

/**
 * Resolves and applies the initial theme synchronously. Call once, as early
 * as possible during bootstrap, so the correct theme is set before first
 * paint (no flash of the wrong color scheme).
 */
export function initTheme(): void {
  if (initialized) {
    return
  }
  initialized = true

  const stored = getStorageItem<Theme>(STORAGE_KEY)
  const media = window.matchMedia('(prefers-color-scheme: dark)')
  applyTheme(stored ?? (media.matches ? 'dark' : 'light'))

  // Follow OS changes only while the user has expressed no explicit preference.
  media.addEventListener('change', (event) => {
    if (getStorageItem<Theme>(STORAGE_KEY) === null) {
      applyTheme(event.matches ? 'dark' : 'light')
    }
  })
}

/**
 * Dark-mode controller backed by the `dark` class on `<html>`.
 *
 * @returns The read-only reactive `theme` plus `toggle` and `setTheme`.
 */
export function useTheme() {
  /**
   * Sets and persists an explicit theme preference.
   *
   * @param value - The theme to activate.
   */
  function setTheme(value: Theme): void {
    applyTheme(value)
    setStorageItem(STORAGE_KEY, value)
  }

  /**
   * Toggles between light and dark themes, persisting the choice.
   */
  function toggle(): void {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return { theme: readonly(theme), toggle, setTheme }
}
