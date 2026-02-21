import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(amount)
}

export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHr = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHr / 24)

  if (diffSec < 60) return "just now"
  if (diffMin < 60) return `${diffMin}m ago`
  if (diffHr < 24) return `${diffHr}h ago`
  if (diffDay < 7) return `${diffDay}d ago`
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" })
}

export function statusColor(status: string): string {
  switch (status) {
    case "AI_APPROVED":
    case "HUMAN_APPROVED":
    case "COMPLETED":
      return "text-green-600 bg-green-50 border-green-200"
    case "AI_DENIED":
    case "HUMAN_DENIED":
    case "FAILED":
      return "text-red-600 bg-red-50 border-red-200"
    case "HUMAN_NEEDED":
      return "text-amber-600 bg-amber-50 border-amber-200"
    case "PENDING_EVALUATION":
      return "text-blue-600 bg-blue-50 border-blue-200"
    case "HUMAN_TIMEOUT":
    case "EXPIRED":
      return "text-gray-600 bg-gray-50 border-gray-200"
    default:
      return "text-gray-600 bg-gray-50 border-gray-200"
  }
}
