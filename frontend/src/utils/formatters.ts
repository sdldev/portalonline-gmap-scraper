import type { JobStatus } from "@/types"

/**
 * Map a JobStatus to a BaseBadge variant string.
 */
export function statusVariant(
  status: JobStatus
): "default" | "success" | "warning" | "danger" | "info" {
  const map: Record<JobStatus, "default" | "success" | "warning" | "danger" | "info"> = {
    queued: "warning",
    running: "info",
    completed: "success",
    failed: "danger",
    cancelled: "default",
  }
  return map[status] || "default"
}

/**
 * Relative time string (e.g. "5m ago", "2h ago").
 */
export function relativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

/**
 * Locale-formatted date string.
 */
export function relativeDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}

/**
 * Mask an API key showing only first 4 and last 4 chars.
 */
export function maskApiKey(key: string): string {
  if (!key || key.length < 8) return key
  return key.slice(0, 4) + "****" + key.slice(-4)
}

/**
 * Copy text to clipboard.
 */
export function copyToClipboard(text: string): void {
  navigator.clipboard.writeText(text)
}
