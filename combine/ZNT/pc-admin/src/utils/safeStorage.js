// A corrupt or unavailable local cache must not prevent opening the application.
export function readStoredObject(key, storage = globalThis.localStorage) {
  try {
    const value = JSON.parse(storage.getItem(key) || 'null')
    return value && typeof value === 'object' && !Array.isArray(value) ? value : null
  } catch { return null }
}
