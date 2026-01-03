/**
 * Downloads a blob as a file
 * @param blob - The blob to download
 * @param filename - The filename to save as
 */
export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()

  // Cleanup
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

/**
 * Generates a timestamped filename
 * @param prefix - Filename prefix (e.g., "validation_report")
 * @param extension - File extension without dot (e.g., "xlsx")
 * @returns Timestamped filename (e.g., "validation_report_2026-01-02.xlsx")
 */
export const generateTimestampedFilename = (prefix: string, extension: string): string => {
  const date = new Date().toISOString().split('T')[0]
  return `${prefix}_${date}.${extension}`
}
