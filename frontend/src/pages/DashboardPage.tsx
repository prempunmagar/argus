import { useState } from "react"
import { Wifi, WifiOff } from "lucide-react"
import { TransactionFeed } from "@/components/transactions/TransactionFeed"
import { useTransactions } from "@/hooks/useTransactions"
import type { TransactionStatus } from "@/lib/types"

type Filter = "all" | "approved" | "denied" | "pending" | "completed"

const FILTER_STATUSES: Record<Filter, TransactionStatus[] | null> = {
  all: null,
  pending: ["PENDING_EVALUATION", "HUMAN_NEEDED"],
  approved: ["AI_APPROVED", "HUMAN_APPROVED"],
  denied: ["AI_DENIED", "HUMAN_DENIED"],
  completed: ["COMPLETED", "EXPIRED", "HUMAN_TIMEOUT", "FAILED"],
}

const FILTER_LABELS: { key: Filter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "denied", label: "Denied" },
  { key: "completed", label: "Completed" },
]

export function DashboardPage() {
  const { transactions, loading, connected } = useTransactions()
  const [filter, setFilter] = useState<Filter>("all")

  const filtered =
    FILTER_STATUSES[filter] === null
      ? transactions
      : transactions.filter((t) => FILTER_STATUSES[filter]!.includes(t.status))

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Live transaction feed from your AI agents
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          {connected ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-green-600" />
              <span className="text-green-600 font-medium">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Offline</span>
            </>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 mb-4 overflow-x-auto">
        {FILTER_LABELS.map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setFilter(key)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap ${
              filter === key
                ? "bg-foreground text-background"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <TransactionFeed transactions={filtered} loading={loading} />
    </div>
  )
}
