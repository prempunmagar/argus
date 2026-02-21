import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { TransactionStatus } from "@/lib/types"

const config: Record<
  TransactionStatus,
  { label: string; className: string; pulse?: boolean }
> = {
  APPROVED: {
    label: "Approved",
    className: "bg-green-50 text-green-700 border-green-200",
  },
  DENIED: {
    label: "Denied",
    className: "bg-red-50 text-red-700 border-red-200",
  },
  PENDING_APPROVAL: {
    label: "Pending Approval",
    className: "bg-amber-50 text-amber-700 border-amber-200",
  },
  PENDING_EVALUATION: {
    label: "Evaluating",
    className: "bg-blue-50 text-blue-700 border-blue-200",
    pulse: true,
  },
  COMPLETED: {
    label: "Completed",
    className: "bg-green-50 text-green-700 border-green-200",
  },
  EXPIRED: {
    label: "Expired",
    className: "bg-gray-50 text-gray-600 border-gray-200",
  },
  FAILED: {
    label: "Failed",
    className: "bg-red-50 text-red-700 border-red-200",
  },
}

export function StatusBadge({ status }: { status: TransactionStatus }) {
  const c = config[status] ?? config.PENDING_EVALUATION
  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-medium", c.className, c.pulse && "animate-pulse")}
    >
      {c.label}
    </Badge>
  )
}
